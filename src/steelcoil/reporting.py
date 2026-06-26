from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from .case_model import SteelCoilCase
from .fusion import CaseFusionResult


def write_case_report_json(case_obj: SteelCoilCase, fusion: CaseFusionResult, output_root: Path) -> Path:
    report_dir = Path(output_root) / case_obj.case_id
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "case_report.json"
    data = {
        "case": asdict(case_obj),
        "fusion": asdict(fusion),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_case_report_md(case_obj: SteelCoilCase, fusion: CaseFusionResult, output_root: Path) -> Path:
    report_dir = Path(output_root) / case_obj.case_id
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "case_report.md"

    lines = [
        f"# Case Report: {case_obj.case_id}",
        "",
        f"- 日期：{case_obj.date}",
        f"- 時間：{case_obj.time}",
        f"- 車牌：{case_obj.plate}",
        f"- 圖片數：{len(case_obj.images)}",
        f"- 狀態：{fusion.status}",
        f"- Coil ID：{fusion.selected_coil_id or 'UNKNOWN'}",
        "",
        "## Cameras",
        "",
    ]

    for image in case_obj.images:
        lines.append(f"- {image.camera}: {image.filename}")

    lines.extend(["", "## Object Counts", ""])
    if fusion.object_counts:
        for label, count in sorted(fusion.object_counts.items()):
            cameras = ", ".join(fusion.cameras_by_label.get(label, []))
            lines.append(f"- {label}: {count} ({cameras})")
    else:
        lines.append("- No detections yet.")

    lines.extend(["", "## Coil ID Candidates", ""])
    if fusion.coil_id_candidates:
        for item in fusion.coil_id_candidates:
            lines.append(f"- {item['camera']}: {item['text']} ({item['confidence']:.3f})")
    else:
        lines.append("- No OCR results yet.")

    lines.extend(["", "## Review Reasons", ""])
    if fusion.review_reasons:
        for reason in fusion.review_reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- None")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
