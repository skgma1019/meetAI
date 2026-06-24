from __future__ import annotations

# Maps each behavior label to the event counter it increments in the scoring API.
_LABEL_TO_EVENT: dict[str, str] = {
    "B01": "hand_movement_events",       # 손동작(머리)
    "B02": "hand_movement_events",       # 손동작(얼굴)
    "B03": "meaningless_gesture_events", # 손동작(몸긁기)
    "B04": "meaningless_gesture_events", # 손동작(손톱)
    "B05": "head_movement_events",       # 머리동작(고개흔들기)
    "B06": "head_movement_events",       # 머리동작(좌우흔들기)
    "B07": "head_movement_events",       # 머리동작(숙이기)
    "B08": "hand_movement_events",       # 팔동작(뒷짐)
    "B09": "meaningless_gesture_events", # 팔동작(무의미반동)
    "B10": "posture_shift_events",       # 자세(좌우흔들기)
    "B11": "posture_shift_events",       # 자세(비스듬히)
    "B12": "posture_shift_events",       # 자세(비비꼬기)
}

EVENT_KEYS: list[str] = [
    "hand_movement_events",
    "head_movement_events",
    "posture_shift_events",
    "meaningless_gesture_events",
]


def labels_to_event_counts(label_sequence: list[str]) -> dict[str, int]:
    """Aggregate per-clip behavior labels into event counts for scoring."""
    counts: dict[str, int] = {k: 0 for k in EVENT_KEYS}
    for label in label_sequence:
        event = _LABEL_TO_EVENT.get(label)
        if event:
            counts[event] += 1
    return counts
