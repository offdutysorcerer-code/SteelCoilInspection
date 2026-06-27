from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Detection:
    camera: str
    image: str
    label: str
    confidence: float
    box_xyxy: list[float]


@dataclass
class OCRResult:
    camera: str
    image: str
    text: str
    confidence: float


@dataclass
class CaseFusionResult:
    case_id: str
    object_counts: dict[str, int] = field(default_factory=dict)
    cameras_by_label: dict[str, list[str]] = field(default_factory=dict)
    coil_id_candidates: list[dict[str, Any]] = field(default_factory=list)
    selected_coil_id: str | None = None
    status: str = "UNKNOWN"
    review_reasons: list[str] = field(default_factory=list)


def fuse_case_results(
    case_id: str,
    detections: list[Detection],
    ocr_results: list[OCRResult],
    min_confidence: float = 0.25,
) -> CaseFusionResult:
    valid_detections = [d for d in detections if d.confidence >= min_confidence]

    object_counts = Counter(d.label for d in valid_detections)
    camera_sets: dict[str, set[str]] = defaultdict(set)
    for d in valid_detections:
        camera_sets[d.label].add(d.camera)

    valid_ocr = [r for r in ocr_results if r.text.strip()]
    text_votes = Counter(r.text.strip() for r in valid_ocr)
    selected_coil_id = text_votes.most_common(1)[0][0] if text_votes else None

    result = CaseFusionResult(
        case_id=case_id,
        object_counts=dict(object_counts),
        cameras_by_label={k: sorted(v) for k, v in camera_sets.items()},
        coil_id_candidates=[
            {"camera": r.camera, "image": r.image, "text": r.text, "confidence": r.confidence}
            for r in valid_ocr
        ],
        selected_coil_id=selected_coil_id,
        status="PASS",
        review_reasons=[],
    )

    if object_counts.get("coil", 0) == 0:
        result.status = "REVIEW"
        result.review_reasons.append("No coil detected in any camera.")

    if not selected_coil_id:
        result.status = "REVIEW"
        result.review_reasons.append("No readable Coil ID found.")

    if len(text_votes) > 1:
        result.status = "REVIEW"
        result.review_reasons.append("Multiple different Coil ID candidates found.")

    for label in ["rubber_pad", "wood", "chain", "strap"]:
        if object_counts.get(label, 0) == 0:
            result.status = "REVIEW"
            result.review_reasons.append(f"No {label} detected in any camera.")

    return result
