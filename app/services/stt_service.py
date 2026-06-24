from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

_model: Any = None
_MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")
_WHISPER_SR = 16000

import torch as _torch
_DEVICE = "cuda" if _torch.cuda.is_available() else "cpu"
_FP16   = _DEVICE == "cuda"

# Use a stable temp dir under the project root (avoids 3rd-party TEMP overrides)
_TEMP_DIR = Path(__file__).resolve().parent.parent.parent / "temp"
_TEMP_DIR.mkdir(exist_ok=True)


def _get_model() -> Any:
    global _model
    if _model is not None:
        return _model
    try:
        import whisper
        _model = whisper.load_model(_MODEL_SIZE, device=_DEVICE)
        print(f"[meetAI] Whisper {_MODEL_SIZE} loaded on {_DEVICE.upper()}", flush=True)
    except ImportError as exc:
        raise RuntimeError(
            "openai-whisper가 설치되지 않았습니다. "
            "`pip install openai-whisper` 를 실행하세요."
        ) from exc
    return _model


def _ffmpeg_to_pcm(path: str) -> np.ndarray:
    """Run ffmpeg to decode any audio/video file → 16 kHz mono float32 PCM."""
    cmd = [
        "ffmpeg", "-nostdin", "-threads", "0",
        "-i", path,
        "-f", "s16le", "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(_WHISPER_SR),
        "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace")
        if "no audio" in stderr.lower():
            raise RuntimeError("업로드한 영상에 오디오 트랙이 없습니다. 음성이 포함된 파일인지 확인하세요.") from e
        raise RuntimeError(f"오디오 디코딩 실패: {stderr[-300:]}") from e
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg을 찾을 수 없습니다. ffmpeg을 설치하고 PATH에 추가해주세요.") from e

    raw = result.stdout
    if not raw:
        raise RuntimeError("업로드한 파일에서 오디오를 추출하지 못했습니다. 오디오 트랙이 있는 파일인지 확인하세요.")

    return np.frombuffer(raw, np.int16).flatten().astype(np.float32) / 32768.0


def _load_audio_numpy(path: str | Path) -> np.ndarray:
    """Load any audio/video file to a 16 kHz mono float32 array."""
    import soundfile as sf

    try:
        audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if sr != _WHISPER_SR:
            n_out = int(len(audio) * _WHISPER_SR / sr)
            audio = np.interp(
                np.linspace(0, len(audio) - 1, n_out),
                np.arange(len(audio)),
                audio,
            ).astype(np.float32)
        return audio
    except Exception:
        return _ffmpeg_to_pcm(str(path))


def transcribe(audio_path: str | Path) -> dict[str, Any]:
    model = _get_model()
    audio = _load_audio_numpy(audio_path)
    result = model.transcribe(audio, language="ko", fp16=_FP16)
    text: str = result.get("text", "").strip()
    segments: list = result.get("segments", [])
    duration_sec: float | None = segments[-1]["end"] if segments else None
    # avg_logprob: Whisper 전사 신뢰도, 발음 평가에 재사용 (범위 ≈ -2.0~0.0)
    avg_logprob: float | None = (
        sum(s["avg_logprob"] for s in segments) / len(segments) if segments else None
    )
    return {"text": text, "duration_sec": duration_sec, "avg_logprob": avg_logprob}


def transcribe_bytes(data: bytes, suffix: str = ".wav") -> dict[str, Any]:
    """Write bytes to a stable temp file, transcribe, then clean up."""
    tmp_path = _TEMP_DIR / f"stt_{os.getpid()}_{id(data)}{suffix}"
    try:
        tmp_path.write_bytes(data)
        return transcribe(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)
