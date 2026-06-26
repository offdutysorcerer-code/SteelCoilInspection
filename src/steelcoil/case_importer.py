from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Iterable

from .paths import IMAGE_EXTENSIONS

CAM_PATTERN = re.compile(r"cam\s*0?([1-9][0-9]?)", re.IGNORECASE)


@dataclass(frozen=True)
class CaseImage:
    case_id: str
    camera: str
    source_path: Path


def detect_camera_name(path: Path) -> str:
    match = CAM_PATTERN.search(path.stem)
    if match:
        return f"cam{int(match.group(1)):02d}"
    return "cam_unknown"


def iter_case_images(raw_dir: Path) -> Iterable[CaseImage]:
    raw_dir = Path(raw_dir)
    for image_path in sorted(raw_dir.rglob("*")):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        case_id = image_path.parent.name
        camera = detect_camera_name(image_path)
        yield CaseImage(case_id=case_id, camera=camera, source_path=image_path)


def prepare_labeling_images(raw_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in iter_case_images(raw_dir):
        target_name = f"{item.case_id}__{item.camera}__{item.source_path.name}"
        shutil.copy2(item.source_path, out_dir / target_name)
        count += 1
    return count
