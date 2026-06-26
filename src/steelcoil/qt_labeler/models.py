from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid


@dataclass
class Box:
    id: str
    label: str
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def create(cls, label: str, x: float, y: float, width: float, height: float) -> "Box":
        return cls(id=str(uuid.uuid4()), label=label, x=x, y=y, width=width, height=height)


@dataclass
class ImageAnnotation:
    image_path: str
    boxes: list[Box] = field(default_factory=list)


@dataclass
class CaseAnnotation:
    case_id: str
    annotations: dict[str, ImageAnnotation] = field(default_factory=dict)

    def get_image_annotation(self, image_path: Path) -> ImageAnnotation:
        key = str(image_path)
        if key not in self.annotations:
            self.annotations[key] = ImageAnnotation(image_path=key)
        return self.annotations[key]


def annotation_path_for_case(case_dir: Path) -> Path:
    return Path(case_dir) / ".steelcoil_annotations.json"


def load_case_annotation(case_dir: Path) -> CaseAnnotation:
    case_dir = Path(case_dir)
    path = annotation_path_for_case(case_dir)
    if not path.exists():
        return CaseAnnotation(case_id=case_dir.name)

    data = json.loads(path.read_text(encoding="utf-8"))
    ann = CaseAnnotation(case_id=data.get("case_id", case_dir.name))
    for image_path, item in data.get("annotations", {}).items():
        ann.annotations[image_path] = ImageAnnotation(
            image_path=image_path,
            boxes=[Box(**box) for box in item.get("boxes", [])],
        )
    return ann


def save_case_annotation(case_dir: Path, annotation: CaseAnnotation) -> Path:
    path = annotation_path_for_case(case_dir)
    data = {
        "case_id": annotation.case_id,
        "annotations": {
            image_path: {
                "image_path": item.image_path,
                "boxes": [box.__dict__ for box in item.boxes],
            }
            for image_path, item in annotation.annotations.items()
        },
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
