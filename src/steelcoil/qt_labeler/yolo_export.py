from __future__ import annotations

from pathlib import Path
import shutil

from PySide6.QtGui import QImage

from .models import CaseAnnotation

LABELS = [
    "coil",
    "coil_id_text",
    "rubber_pad",
    "chain",
    "strap",
    "tarp",
    "wood_block",
    "trailer",
]


def export_case_to_yolo(annotation: CaseAnnotation, output_dir: Path) -> None:
    output_dir = Path(output_dir)
    image_dir = output_dir / "images" / "train"
    label_dir = output_dir / "labels" / "train"
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    for image_path_text, image_ann in annotation.annotations.items():
        image_path = Path(image_path_text)
        if not image_path.exists():
            continue

        image = QImage(str(image_path))
        if image.isNull():
            continue
        width = image.width()
        height = image.height()

        target_image = image_dir / image_path.name
        shutil.copy2(image_path, target_image)

        rows = []
        for box in image_ann.boxes:
            if box.label not in LABELS:
                continue
            class_id = LABELS.index(box.label)
            x_center = (box.x + box.width / 2) / width
            y_center = (box.y + box.height / 2) / height
            box_width = box.width / width
            box_height = box.height / height
            rows.append(f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}")

        label_path = label_dir / f"{image_path.stem}.txt"
        label_path.write_text("\n".join(rows), encoding="utf-8")

    names = "\n".join(f"  {i}: {name}" for i, name in enumerate(LABELS))
    yaml_text = f"path: {output_dir.resolve()}\ntrain: images/train\nval: images/train\nnames:\n{names}\n"
    (output_dir / "steel_coil.yaml").write_text(yaml_text, encoding="utf-8")
