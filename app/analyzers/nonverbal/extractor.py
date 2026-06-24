from __future__ import annotations

import math
from typing import Any


# Keypoint index mapping (COCO-18 style)
_NOSE = 0
_NECK = 5
_L_SHOULDER = 6
_R_SHOULDER = 7
_L_ELBOW = 8
_R_ELBOW = 9
_L_WRIST = 10
_R_WRIST = 11
_L_HIP = 12
_R_HIP = 13

FEATURE_NAMES: list[str] = [
    "lw_nose_dist",
    "rw_nose_dist",
    "lw_neck_dist",
    "rw_neck_dist",
    "lw_hip_dist",
    "rw_hip_dist",
    "lw_above_nose",
    "rw_above_nose",
    "lw_above_shoulder",
    "rw_above_shoulder",
    "le_above_shoulder",
    "re_above_shoulder",
    "shoulder_tilt",
    "head_lean_x",
    "head_lean_y",
    "hip_shoulder_x",
    "nose_x_var",
    "nose_y_var",
    "lw_x_var",
    "lw_y_var",
    "rw_x_var",
    "rw_y_var",
    "hip_cx_var",
    "shoulder_tilt_var",
    "lw_nose_dist_var",
    "rw_nose_dist_var",
]


def _dist2d(a: list[float], b: list[float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _var(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _midpoint(a: list[float], b: list[float]) -> list[float]:
    return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]


def extract_clip_features(frames: list[list[list[float]]]) -> dict[str, float]:
    """Extract biomechanical features from a clip (list of frames).

    Each frame is a list of 18 keypoints, each keypoint is [x, y, z].
    All distances are normalized by shoulder width.
    """
    if not frames:
        return {name: 0.0 for name in FEATURE_NAMES}

    per_frame_lw_nose: list[float] = []
    per_frame_rw_nose: list[float] = []
    per_frame_lw_neck: list[float] = []
    per_frame_rw_neck: list[float] = []
    per_frame_lw_hip: list[float] = []
    per_frame_rw_hip: list[float] = []
    per_frame_lw_above_nose: list[float] = []
    per_frame_rw_above_nose: list[float] = []
    per_frame_lw_above_shoulder: list[float] = []
    per_frame_rw_above_shoulder: list[float] = []
    per_frame_le_above_shoulder: list[float] = []
    per_frame_re_above_shoulder: list[float] = []
    per_frame_shoulder_tilt: list[float] = []
    per_frame_head_lean_x: list[float] = []
    per_frame_head_lean_y: list[float] = []
    per_frame_hip_shoulder_x: list[float] = []
    per_frame_nose_x: list[float] = []
    per_frame_nose_y: list[float] = []
    per_frame_lw_x: list[float] = []
    per_frame_lw_y: list[float] = []
    per_frame_rw_x: list[float] = []
    per_frame_rw_y: list[float] = []
    per_frame_hip_cx: list[float] = []

    for frame in frames:
        if len(frame) < 14:
            continue

        nose = frame[_NOSE]
        neck = frame[_NECK]
        l_sh = frame[_L_SHOULDER]
        r_sh = frame[_R_SHOULDER]
        l_elb = frame[_L_ELBOW]
        r_elb = frame[_R_ELBOW]
        l_wr = frame[_L_WRIST]
        r_wr = frame[_R_WRIST]
        l_hip = frame[_L_HIP]
        r_hip = frame[_R_HIP]

        shoulder_w = _dist2d(l_sh, r_sh) or 1.0
        hip_cx = (l_hip[0] + r_hip[0]) / 2
        hip_cy = (l_hip[1] + r_hip[1]) / 2
        sh_cx = (l_sh[0] + r_sh[0]) / 2

        per_frame_lw_nose.append(_dist2d(l_wr, nose) / shoulder_w)
        per_frame_rw_nose.append(_dist2d(r_wr, nose) / shoulder_w)
        per_frame_lw_neck.append(_dist2d(l_wr, neck) / shoulder_w)
        per_frame_rw_neck.append(_dist2d(r_wr, neck) / shoulder_w)
        per_frame_lw_hip.append(_dist2d(l_wr, l_hip) / shoulder_w)
        per_frame_rw_hip.append(_dist2d(r_wr, r_hip) / shoulder_w)

        per_frame_lw_above_nose.append(1.0 if l_wr[1] < nose[1] else 0.0)
        per_frame_rw_above_nose.append(1.0 if r_wr[1] < nose[1] else 0.0)
        per_frame_lw_above_shoulder.append(1.0 if l_wr[1] < l_sh[1] else 0.0)
        per_frame_rw_above_shoulder.append(1.0 if r_wr[1] < r_sh[1] else 0.0)
        per_frame_le_above_shoulder.append(1.0 if l_elb[1] < l_sh[1] else 0.0)
        per_frame_re_above_shoulder.append(1.0 if r_elb[1] < r_sh[1] else 0.0)

        per_frame_shoulder_tilt.append((l_sh[1] - r_sh[1]) / shoulder_w)
        per_frame_head_lean_x.append((nose[0] - neck[0]) / shoulder_w)
        per_frame_head_lean_y.append((nose[1] - neck[1]) / shoulder_w)
        per_frame_hip_shoulder_x.append((hip_cx - sh_cx) / shoulder_w)

        per_frame_nose_x.append(nose[0] / shoulder_w)
        per_frame_nose_y.append(nose[1] / shoulder_w)
        per_frame_lw_x.append(l_wr[0] / shoulder_w)
        per_frame_lw_y.append(l_wr[1] / shoulder_w)
        per_frame_rw_x.append(r_wr[0] / shoulder_w)
        per_frame_rw_y.append(r_wr[1] / shoulder_w)
        per_frame_hip_cx.append(hip_cx / shoulder_w)

    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return {
        "lw_nose_dist": _mean(per_frame_lw_nose),
        "rw_nose_dist": _mean(per_frame_rw_nose),
        "lw_neck_dist": _mean(per_frame_lw_neck),
        "rw_neck_dist": _mean(per_frame_rw_neck),
        "lw_hip_dist": _mean(per_frame_lw_hip),
        "rw_hip_dist": _mean(per_frame_rw_hip),
        "lw_above_nose": _mean(per_frame_lw_above_nose),
        "rw_above_nose": _mean(per_frame_rw_above_nose),
        "lw_above_shoulder": _mean(per_frame_lw_above_shoulder),
        "rw_above_shoulder": _mean(per_frame_rw_above_shoulder),
        "le_above_shoulder": _mean(per_frame_le_above_shoulder),
        "re_above_shoulder": _mean(per_frame_re_above_shoulder),
        "shoulder_tilt": _mean(per_frame_shoulder_tilt),
        "head_lean_x": _mean(per_frame_head_lean_x),
        "head_lean_y": _mean(per_frame_head_lean_y),
        "hip_shoulder_x": _mean(per_frame_hip_shoulder_x),
        "nose_x_var": _var(per_frame_nose_x),
        "nose_y_var": _var(per_frame_nose_y),
        "lw_x_var": _var(per_frame_lw_x),
        "lw_y_var": _var(per_frame_lw_y),
        "rw_x_var": _var(per_frame_rw_x),
        "rw_y_var": _var(per_frame_rw_y),
        "hip_cx_var": _var(per_frame_hip_cx),
        "shoulder_tilt_var": _var(per_frame_shoulder_tilt),
        "lw_nose_dist_var": _var(per_frame_lw_nose),
        "rw_nose_dist_var": _var(per_frame_rw_nose),
    }


def frames_from_annotation(annotation: list[dict[str, Any]]) -> list[list[list[float]]]:
    """Convert raw JSON annotation list to list of keypoint frames."""
    frames = []
    for item in annotation:
        kps = item.get("keypoints", [])
        if isinstance(kps, list) and kps:
            frames.append([[float(v) for v in kp[:3]] for kp in kps])
    return frames
