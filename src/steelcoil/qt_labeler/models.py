from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
import uuid

from ..case_model import parse_case_id

SCHEMA_VERSION = 2
CAMERA_PATTERN = re.compile(r"_(cam\d+)\.", re.IGNORECASE)


@dataclass
class Box:
    id: str
    label: str
    x: float
    y: float
    width: float
    height: float
    track_id: str | None = None
    parent_track_id: str | None = None

    @classmethod
    def create(
        cls,
        label: str,
        x: float,
        y: float,
        width: float,
        height: float,
        track_id: str | None = None,
        parent_track_id: str | None = None,
    ) -> "Box":
        return cls(
            id=str(uuid.uuid4()),
            label=label,
            x=x,
            y=y,
            width=width,
            height=height,
            track_id=track_id,
            parent_track_id=parent_track_id,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Box":
        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            label=data.get("label", "coil"),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", data.get("w", 0))),
            height=float(data.get("height", data.get("h", 0))),
            track_id=data.get("track_id"),
            parent_track_id=data.get("parent_track_id"),
        )

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        if self.track_id:
            data["track_id"] = self.track_id
        if self.parent_track_id:
            data["parent_track_id"] = self.parent_track_id
        return data


@dataclass
class Coil:
    track_id: str
    display_name: str
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Coil":
        return cls(
            track_id=data.get("track_id") or f"coil_{uuid.uuid4().hex[:8]}",
            display_name=data.get("display_name") or data.get("track_id") or "Coil",
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "display_name": self.display_name,
            "notes": self.notes,
        }


@dataclass
class ImageAnnotation:
    image_path: str
    camera: str = ""
    filename: str = ""
    boxes: list[Box] = field(default_factory=list)


@dataclass
class CaseAnnotation:
    case_id: str
    date: str = ""
    time: str = ""
    plate: str = ""
    coils: list[Coil] = field(default_factory=list)
    annotations: dict[str, ImageAnnotation] = field(default_factory=dict)

    def get_image_annotation(self, image_path: Path) -> ImageAnnotation:
        key = str(image_path)
        if key not in self.annotations:
            self.annotations[key] = ImageAnnotation(
                image_path=key,
                camera=detect_camera_from_path(image_path),
                filename=Path(image_path).name,
            )
        return self.annotations[key]

    def coil_by_track_id(self, track_id: str | None) -> Coil | None:
        if not track_id:
            return None
        for coil in self.coils:
            if coil.track_id == track_id:
                return coil
        return None

    def next_coil_number(self) -> int:
        return len(self.coils) + 1

    def create_coil(self) -> Coil:
        number = self.next_coil_number()
        existing = {coil.track_id for coil in self.coils}
        while True:
            track_id = f"coil_{number:03d}"
            if track_id not in existing:
                break
            number += 1
        coil = Coil(track_id=track_id, display_name=f"Coil #{number}")
        self.coils.append(coil)
        return coil

    def ensure_coil(self, track_id: str | None = None) -> Coil:
        if track_id:
            existing = self.coil_by_track_id(track_id)
            if existing:
                return existing
        return self.create_coil()

    def normalize_coils_from_boxes(self) -> None:
        known = {coil.track_id for coil in self.coils}
        for image_ann in self.annotations.values():
            for box in image_ann.boxes:
                if box.label == "coil" and box.track_id and box.track_id not in known:
                    number = len(self.coils) + 1
                    self.coils.append(Coil(track_id=box.track_id, display_name=f"Coil #{number}"))
                    known.add(box.track_id)


def detect_camera_from_path(image_path: str | Path) -> str:
    name = Path(image_path).name
    match = CAMERA_PATTERN.search(name)
    if match:
        return match.group(1).lower()
    return Path(image_path).stem


def annotation_path_for_case(case_dir: Path) -> Path:
    return Path(case_dir) / ".steelcoil_annotations.json"


def load_case_annotation(case_dir: Path) -> CaseAnnotation:
    case_dir = Path(case_dir)
    path = annotation_path_for_case(case_dir)
    if not path.exists():
        date, time, plate = parse_case_id(case_dir.name)
        return CaseAnnotation(case_id=case_dir.name, date=date, time=time, plate=plate)

    data = json.loads(path.read_text(encoding="utf-8"))
    schema_version = int(data.get("schema_version", 1))
    if schema_version >= 2:
        ann = load_schema_v2(case_dir, data)
    else:
        ann = load_legacy_schema(case_dir, data)
    ann.normalize_coils_from_boxes()
    return ann


def load_legacy_schema(case_dir: Path, data: dict) -> CaseAnnotation:
    case_id = data.get("case_id", case_dir.name)
    date, time, plate = parse_case_id(case_id)
    ann = CaseAnnotation(case_id=case_id, date=date, time=time, plate=plate)
    for image_path, item in data.get("annotations", {}).items():
        path = Path(image_path)
        ann.annotations[image_path] = ImageAnnotation(
            image_path=image_path,
            camera=detect_camera_from_path(path),
            filename=path.name,
            boxes=[Box.from_dict(box) for box in item.get("boxes", [])],
        )
    return ann


def load_schema_v2(case_dir: Path, data: dict) -> CaseAnnotation:
    case_data = data.get("case", {})
    case_id = case_data.get("case_id") or data.get("case_id") or case_dir.name
    date, time, plate = parse_case_id(case_id)
    ann = CaseAnnotation(
        case_id=case_id,
        date=case_data.get("date", date),
        time=case_data.get("time", time),
        plate=case_data.get("plate", plate),
        coils=[Coil.from_dict(coil) for coil in data.get("coils", [])],
    )
    for item in data.get("images", []):
        image_path = item.get("image_path")
        if not image_path:
            filename = item.get("filename", "")
            image_path = str(case_dir / filename) if filename else ""
        if not image_path:
            continue
        path = Path(image_path)
        ann.annotations[image_path] = ImageAnnotation(
            image_path=image_path,
            camera=item.get("camera") or detect_camera_from_path(path),
            filename=item.get("filename") or path.name,
            boxes=[Box.from_dict(box) for box in item.get("boxes", [])],
        )
    return ann


def save_case_annotation(case_dir: Path, annotation: CaseAnnotation) -> Path:
    path = annotation_path_for_case(case_dir)
    date, time, plate = parse_case_id(annotation.case_id)
    annotation.date = annotation.date or date
    annotation.time = annotation.time or time
    annotation.plate = annotation.plate or plate
    annotation.normalize_coils_from_boxes()

    images = []
    for image_path, item in annotation.annotations.items():
        image_path_obj = Path(image_path)
        images.append(
            {
                "camera": item.camera or detect_camera_from_path(image_path_obj),
                "filename": item.filename or image_path_obj.name,
                "image_path": item.image_path,
                "boxes": [box.to_dict() for box in item.boxes],
            }
        )

    data = {
        "schema_version": SCHEMA_VERSION,
        "case": {
            "case_id": annotation.case_id,
            "date": annotation.date,
            "time": annotation.time,
            "plate": annotation.plate,
        },
        "coils": [coil.to_dict() for coil in annotation.coils],
        "images": images,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
