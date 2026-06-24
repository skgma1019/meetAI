from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

import cv2
import numpy as np

# MediaPipe Pose landmark indices (33개)
_NOSE           = 0
_LEFT_EYE       = 2
_RIGHT_EYE      = 5
_LEFT_SHOULDER  = 11
_RIGHT_SHOULDER = 12
_LEFT_WRIST     = 15
_RIGHT_WRIST    = 16
_LEFT_HIP       = 23
_RIGHT_HIP      = 24

# 상체 유효 프레임 판정 기준 — 얼굴 3개 + 어깨 2개
_UPPER_BODY_KEY = [_NOSE, _LEFT_EYE, _RIGHT_EYE, _LEFT_SHOULDER, _RIGHT_SHOULDER]
_VIS_THRESH = 0.3


@lru_cache(maxsize=1)
def _get_yolo() -> Any:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    print("[meetAI] YOLOv8n (detection) loaded", flush=True)
    return model


def _new_mp_pose():
    """MediaPipe Pose 인스턴스. 상체만 나오는 영상에 맞게 완화된 설정."""
    import mediapipe as mp
    return mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3,
    )


def _angle_deg(ax: float, ay: float, bx: float, by: float) -> float:
    return math.degrees(math.atan2(by - ay, bx - ax))


def _stability_score(values: list[float], tolerance: float) -> float:
    """표준편차가 낮을수록 100에 가까운 점수. tolerance = 50점 기준 std."""
    if len(values) < 2:
        return 80.0
    std = float(np.std(values))
    score = 100.0 * math.exp(-((std / tolerance) ** 2))
    return round(max(0.0, min(100.0, score)), 2)


def _vis(lms: list, idx: int) -> float:
    """랜드마크 visibility 반환 (0.0~1.0)."""
    return float(getattr(lms[idx], "visibility", 0.0))


def _person_crop(frame: np.ndarray, yolo: Any) -> np.ndarray:
    """
    YOLOv8으로 가장 신뢰도 높은 사람 BBox 크롭.
    conf=0.3으로 낮춰 화면 상단 상체만 있어도 감지.
    """
    try:
        results = yolo(frame, classes=[0], conf=0.3, verbose=False)
        if results and results[0].boxes is not None and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            best = int(boxes.conf.cpu().numpy().argmax())
            x1, y1, x2, y2 = boxes.xyxy.cpu().numpy()[best].astype(int)
            h, w = frame.shape[:2]
            pad = 20
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
            if (x2 - x1) > 30 and (y2 - y1) > 30:
                return frame[y1:y2, x1:x2]
    except Exception as exc:
        print(f"[meetAI] YOLO crop 실패 (폴백 full frame): {exc}", flush=True)
    return frame


def _run_mediapipe(img_bgr: np.ndarray, mp_pose: Any) -> list | None:
    """MediaPipe Pose 실행. 랜드마크 리스트 반환, 실패 시 None."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    result = mp_pose.process(img_rgb)
    if result.pose_landmarks:
        return result.pose_landmarks.landmark
    return None


def _lm(lms: list, idx: int) -> tuple[float, float]:
    return lms[idx].x, lms[idx].y


def _is_valid_frame(lms: list) -> bool:
    """
    상체 기준 유효 프레임 판정.
    얼굴(NOSE, LEFT_EYE, RIGHT_EYE) + 어깨(LEFT_SHOULDER, RIGHT_SHOULDER)
    5개 중 3개 이상 visibility > 0.3이면 유효.
    """
    return sum(1 for idx in _UPPER_BODY_KEY if _vis(lms, idx) > _VIS_THRESH) >= 3


def analyze_video(video_path: str) -> dict:
    """
    YOLOv8 person detection → MediaPipe Pose 33 landmarks 추출.
    1fps 샘플링(최대 10프레임)으로 자세·시선·손동작 점수 산출.
    상체만 나오는 면접/발표 영상 대응: visibility 기반으로 하체 의존 로직 제거.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _no_data_result("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    sample_count = min(10, max(1, int(duration_sec)))
    interval = max(1, total_frames // sample_count)

    yolo: Any = None
    try:
        yolo = _get_yolo()
    except Exception as exc:
        print(f"[meetAI] YOLO 로드 실패 → MediaPipe 단독 사용: {exc}", flush=True)

    mp_pose = _new_mp_pose()

    keypoints_sequence: list[list] = []
    shoulder_tilts: list[float] = []    # posture: 어깨 기울기
    nose_rel_xs: list[float] = []       # gaze: 어깨 중심 기준 코 x 편차
    wrist_rel_ys: list[float] = []      # gesture: 어깨 기준 손목 y (하체 대신)
    wrist_moves: list[float] = []       # gesture: 프레임 간 손목 이동량
    prev_wrist: list[float] = []

    for i in range(sample_count):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
        ret, frame = cap.read()
        if not ret:
            break

        crop = _person_crop(frame, yolo) if yolo is not None else frame

        lms = _run_mediapipe(crop, mp_pose)
        if lms is None:
            lms = _run_mediapipe(frame, mp_pose)
        if lms is None:
            continue

        # 상체 키포인트 기준 유효 프레임 판정
        if not _is_valid_frame(lms):
            continue

        keypoints_sequence.append([[lm.x, lm.y, lm.z] for lm in lms])

        ls_x, ls_y = _lm(lms, _LEFT_SHOULDER)
        rs_x, rs_y = _lm(lms, _RIGHT_SHOULDER)
        ls_vis = _vis(lms, _LEFT_SHOULDER)
        rs_vis = _vis(lms, _RIGHT_SHOULDER)
        shoulder_w = abs(ls_x - rs_x)

        # ── 자세 안정성: 어깨 기울기만 사용 (하체 없어도 계산 가능) ──
        if ls_vis > _VIS_THRESH and rs_vis > _VIS_THRESH:
            shoulder_tilts.append(abs(_angle_deg(rs_x, rs_y, ls_x, ls_y)))

        # ── 시선 안정성: 코 x를 어깨 너비로 정규화 ─────────────────
        nose_x, _ = _lm(lms, _NOSE)
        shoulder_cx = (ls_x + rs_x) / 2.0
        if shoulder_w > 0.01 and ls_vis > _VIS_THRESH and rs_vis > _VIS_THRESH:
            nose_rel_xs.append((nose_x - shoulder_cx) / shoulder_w)

        # ── 손동작: 골반 대신 어깨 기준으로 정규화 ──────────────────
        # 상체만 나오는 영상에서 골반 좌표는 신뢰할 수 없음
        shoulder_cy = (ls_y + rs_y) / 2.0
        ref_scale = max(shoulder_w, 0.05)

        lw_vis = _vis(lms, _LEFT_WRIST)
        rw_vis = _vis(lms, _RIGHT_WRIST)
        lw_x, lw_y = _lm(lms, _LEFT_WRIST)
        rw_x, rw_y = _lm(lms, _RIGHT_WRIST)

        curr_wrist: list[float] = []
        if lw_vis > _VIS_THRESH:
            wrist_rel_ys.append((lw_y - shoulder_cy) / ref_scale)
            curr_wrist.append(lw_x)
        if rw_vis > _VIS_THRESH:
            wrist_rel_ys.append((rw_y - shoulder_cy) / ref_scale)
            curr_wrist.append(rw_x)

        if prev_wrist and curr_wrist:
            n = min(len(prev_wrist), len(curr_wrist))
            wrist_moves.append(
                sum(abs(a - b) for a, b in zip(curr_wrist[:n], prev_wrist[:n])) / n
            )
        prev_wrist = curr_wrist

    mp_pose.close()
    cap.release()

    if not keypoints_sequence:
        return _no_data_result("포즈 랜드마크를 감지하지 못했습니다 (상체가 보이지 않는 영상).")

    # ── 점수 계산 ────────────────────────────────────────────────

    # posture_score: 어깨 기울기 분산 + 평균 패널티
    posture_score: float
    if shoulder_tilts:
        posture_score = _stability_score(shoulder_tilts, tolerance=5.0)
        avg_tilt = float(np.mean(shoulder_tilts))
        posture_score = round(max(0.0, posture_score - min(20.0, avg_tilt * 1.5)), 2)
    else:
        posture_score = 80.0

    # gaze_score: 코 x 편차 (어깨 너비 기준 0.3이 50점 기준)
    gaze_score = _stability_score(nose_rel_xs, tolerance=0.3) if nose_rel_xs else 80.0

    # gesture_score: 손목 위치·이동 안정성. 손이 보이지 않으면 중립 70점
    if wrist_rel_ys:
        pos_score = _stability_score(wrist_rel_ys, tolerance=0.5)
        move_score = _stability_score(wrist_moves, tolerance=0.06) if wrist_moves else 80.0
        gesture_score: float = round(min(100.0, pos_score * 0.5 + move_score * 0.5), 2)
    else:
        gesture_score = 70.0  # 손이 화면에 없음 — 중립값

    nonverbal_score = round(
        posture_score * 0.35 + gaze_score * 0.35 + gesture_score * 0.30,
        2,
    )

    return {
        "keypoints_sequence": keypoints_sequence,
        "posture_score": posture_score,
        "gaze_score": gaze_score,
        "gesture_score": gesture_score,
        "nonverbal_score": nonverbal_score,
        "frame_count": len(keypoints_sequence),
        "duration_sec": round(duration_sec, 2),
    }


def _no_data_result(reason: str = "") -> dict:
    """유효 프레임 없을 때 None 점수 반환 — routes_upload.py에서 비언어 분석 생략 처리."""
    if reason:
        print(f"[meetAI] 포즈 분석 스킵: {reason}", flush=True)
    return {
        "keypoints_sequence": [],
        "posture_score": None,
        "gaze_score": None,
        "gesture_score": None,
        "nonverbal_score": None,
        "frame_count": 0,
        "error": reason,
    }
