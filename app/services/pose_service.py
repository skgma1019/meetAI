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


@lru_cache(maxsize=1)
def _get_yolo() -> Any:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")  # detection 모델 (pose 아님)
    print("[meetAI] YOLOv8n (detection) loaded", flush=True)
    return model


def _new_mp_pose():
    """MediaPipe Pose 인스턴스 생성. static_image_mode=True로 프레임별 독립 처리."""
    import mediapipe as mp
    return mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )


def _angle_deg(ax: float, ay: float, bx: float, by: float) -> float:
    return math.degrees(math.atan2(by - ay, bx - ax))


def _stability_score(values: list[float], tolerance: float) -> float:
    """
    값의 표준편차가 낮을수록 100에 가까운 점수.
    tolerance = 점수 50점에 해당하는 std 기준값.
    """
    if len(values) < 2:
        return 80.0
    std = float(np.std(values))
    score = 100.0 * math.exp(-((std / tolerance) ** 2))
    return round(max(0.0, min(100.0, score)), 2)


def _person_crop(frame: np.ndarray, yolo: Any) -> np.ndarray:
    """
    YOLOv8으로 가장 신뢰도 높은 사람 BBox 크롭.
    감지 실패 시 원본 프레임 반환.
    """
    try:
        results = yolo(frame, classes=[0], verbose=False)  # class 0 = person
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


def analyze_video(video_path: str) -> dict:
    """
    YOLOv8 person detection → MediaPipe Pose 33 landmarks 추출.
    1fps 샘플링(최대 10프레임)으로 자세·시선·손동작 점수 산출.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _default_result("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    sample_count = min(10, max(1, int(duration_sec)))
    interval = max(1, total_frames // sample_count)

    # YOLO 로드 (실패해도 MediaPipe 단독으로 폴백)
    yolo: Any = None
    try:
        yolo = _get_yolo()
    except Exception as exc:
        print(f"[meetAI] YOLO 로드 실패 → MediaPipe 단독 사용: {exc}", flush=True)

    mp_pose = _new_mp_pose()

    keypoints_sequence: list[list] = []
    shoulder_tilts: list[float] = []   # posture
    hip_tilts: list[float] = []        # posture
    nose_rel_xs: list[float] = []      # gaze: 어깨 중심 기준 코 x 편차
    wrist_rel_ys: list[float] = []     # gesture: 엉덩이 기준 손목 y 상대값
    wrist_moves: list[float] = []      # gesture: 프레임 간 손목 이동량
    prev_wrist: list[float] = []

    for i in range(sample_count):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
        ret, frame = cap.read()
        if not ret:
            break

        # 1) YOLO로 사람 크롭
        crop = _person_crop(frame, yolo) if yolo is not None else frame

        # 2) MediaPipe Pose — 크롭 우선, 실패 시 원본 full frame
        lms = _run_mediapipe(crop, mp_pose)
        if lms is None:
            lms = _run_mediapipe(frame, mp_pose)
        if lms is None:
            continue

        # 3) 33개 랜드마크 저장 (정규화 좌표)
        keypoints_sequence.append([[lm.x, lm.y, lm.z] for lm in lms])

        ls_x, ls_y = _lm(lms, _LEFT_SHOULDER)
        rs_x, rs_y = _lm(lms, _RIGHT_SHOULDER)
        lh_x, lh_y = _lm(lms, _LEFT_HIP)
        rh_x, rh_y = _lm(lms, _RIGHT_HIP)

        # ── 자세 안정성 ──────────────────────────────────────────
        # 어깨 기울기 각도 (수평=0도가 이상적)
        shoulder_tilts.append(abs(_angle_deg(rs_x, rs_y, ls_x, ls_y)))
        # 골반 기울기 각도
        hip_tilts.append(abs(_angle_deg(rh_x, rh_y, lh_x, lh_y)))

        # ── 시선 안정성 ──────────────────────────────────────────
        # 코 x를 어깨 너비로 정규화해 절대 위치 의존성 제거
        nose_x, _ = _lm(lms, _NOSE)
        shoulder_cx = (ls_x + rs_x) / 2.0
        shoulder_w = abs(ls_x - rs_x)
        if shoulder_w > 0.01:
            nose_rel_xs.append((nose_x - shoulder_cx) / shoulder_w)

        # ── 손동작 적절성 ─────────────────────────────────────────
        # 손목 y를 골반 기준으로 정규화 (양수 = 골반 아래 = 자연스러움)
        hip_cy = (lh_y + rh_y) / 2.0
        torso_h = max(abs(((ls_y + rs_y) / 2.0) - hip_cy), 0.05)
        lw_x, lw_y = _lm(lms, _LEFT_WRIST)
        rw_x, rw_y = _lm(lms, _RIGHT_WRIST)
        for wy in (lw_y, rw_y):
            wrist_rel_ys.append((wy - hip_cy) / torso_h)

        # 프레임 간 손목 이동량
        curr = [lw_x, rw_x]
        if prev_wrist:
            wrist_moves.append(sum(abs(a - b) for a, b in zip(curr, prev_wrist)))
        prev_wrist = curr

    mp_pose.close()
    cap.release()

    if not keypoints_sequence:
        return _default_result("포즈 랜드마크를 감지하지 못했습니다 (인물이 보이지 않는 영상).")

    # ── 점수 계산 ────────────────────────────────────────────────

    # posture_score: 어깨·골반 기울기 분산 + 평균 기울기 패널티
    all_tilts = shoulder_tilts + hip_tilts
    posture_score = _stability_score(all_tilts, tolerance=5.0)
    if all_tilts:
        avg_tilt = float(np.mean(all_tilts))
        # 평균 기울기 10° 이상이면 최대 20점 감점
        posture_score = round(max(0.0, posture_score - min(20.0, avg_tilt * 1.5)), 2)

    # gaze_score: 코 위치 편차 (어깨 너비 대비 0.3이 50점 기준)
    gaze_score = _stability_score(nose_rel_xs, tolerance=0.3)

    # gesture_score: 손목 위치 안정성 + 손목 이동 안정성 + 골반 아래 비율 보너스
    pos_score  = _stability_score(wrist_rel_ys, tolerance=0.5)
    move_score = _stability_score(wrist_moves, tolerance=0.06) if wrist_moves else 80.0
    below_ratio = (
        sum(1 for y in wrist_rel_ys if y > 0) / len(wrist_rel_ys)
        if wrist_rel_ys else 0.5
    )
    gesture_score = round(
        min(100.0, pos_score * 0.4 + move_score * 0.4 + below_ratio * 20.0),
        2,
    )

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


def _default_result(reason: str = "") -> dict:
    return {
        "keypoints_sequence": [],
        "posture_score": 75.0,
        "gaze_score": 75.0,
        "gesture_score": 75.0,
        "nonverbal_score": 75.0,
        "frame_count": 0,
        "error": reason,
    }
