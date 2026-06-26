import argparse
import json
from pathlib import Path
from urllib.parse import quote

from .case_model import parse_case_id
from .case_importer import detect_camera_name
from .paths import IMAGE_EXTENSIONS, RAW_DIR


def build_task(image_path: Path, raw_root: Path, url_base: str) -> dict:
    image_path = image_path.resolve()
    raw_root = raw_root.resolve()
    rel = image_path.relative_to(raw_root).as_posix()

    case_id = image_path.parent.name
    date, time, plate = parse_case_id(case_id)
    camera = detect_camera_name(image_path)

    encoded_rel = quote(rel, safe="/")
    image_url = f"{url_base.rstrip('/')}/{encoded_rel}"

    return {
        "data": {
            "image": image_url,
            "case_info": f"案件：{case_id}｜日期：{date}｜時間：{time}｜車牌：{plate}｜相機：{camera}｜檔名：{image_path.name}",
            "case_id": case_id,
            "date": date,
            "time": time,
            "plate": plate,
            "camera": camera,
            "filename": image_path.name,
            "relative_path": rel,
        }
    }


def create_tasks(raw_root: Path, output_json: Path, url_base: str) -> int:
    raw_root = raw_root.resolve()
    images = sorted(
        p for p in raw_root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    tasks = [build_task(p, raw_root, url_base) for p in images]
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(tasks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Label Studio import tasks JSON from raw Case folders.")
    parser.add_argument("--raw", default=str(RAW_DIR), help="Raw root. Each subfolder is one case.")
    parser.add_argument("--out", default="data/label_studio_tasks.json")
    parser.add_argument("--url-base", default="http://localhost:8090", help="Base URL of the static image server.")
    args = parser.parse_args()
    count = create_tasks(Path(args.raw), Path(args.out), args.url_base)
    print(f"Wrote {count} Label Studio tasks to {args.out}")
    print(f"Image URL base: {args.url_base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
