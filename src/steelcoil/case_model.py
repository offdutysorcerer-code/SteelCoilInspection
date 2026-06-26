from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Iterable

from .paths import IMAGE_EXTENSIONS
from .case_importer import detect_camera_name

CASE_PATTERN = re.compile(r"^(?P<date>\d{8})_(?P<time>\d{6})_(?P<plate>.+)$")


@dataclass(frozen=True)
class CameraImage:
    camera: str
    path: str
    filename: str


@dataclass(frozen=True)
class SteelCoilCase:
    case_id: str
    date: str
    time: str
    plate: str
    source_dir: str
    images: list[CameraImage]


def parse_case_id(case_id: str) -> tuple[str, str, str]:
    match = CASE_PATTERN.match(case_id)
    if not match:
        return "", "", ""

    raw_date = match.group("date")
    raw_time = match.group("time")
    plate = match.group("plate")

    dt = datetime.strptime(raw_date + raw_time, "%Y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), plate


def scan_case(case_dir: Path) -> SteelCoilCase:
    case_dir = Path(case_dir)
    case_id = case_dir.name
    date, time, plate = parse_case_id(case_id)

    images: list[CameraImage] = []
    for image_path in sorted(case_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        images.append(
            CameraImage(
                camera=detect_camera_name(image_path),
                path=str(image_path),
                filename=image_path.name,
            )
        )

    return SteelCoilCase(
        case_id=case_id,
        date=date,
        time=time,
        plate=plate,
        source_dir=str(case_dir),
        images=images,
    )


def scan_cases(raw_root: Path) -> list[SteelCoilCase]:
    raw_root = Path(raw_root)
    if not raw_root.exists():
        return []
    cases = []
    for item in sorted(raw_root.iterdir()):
        if item.is_dir():
            cases.append(scan_case(item))
    return cases


def write_case_metadata(case_obj: SteelCoilCase, output_dir: Path) -> Path:
    output_dir = Path(output_dir) / case_obj.case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "metadata.json"
    output_path.write_text(json.dumps(asdict(case_obj), ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_all_case_metadata(cases: Iterable[SteelCoilCase], output_root: Path) -> int:
    count = 0
    for case_obj in cases:
        write_case_metadata(case_obj, output_root)
        count += 1
    return count
