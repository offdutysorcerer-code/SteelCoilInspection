import argparse
from pathlib import Path

from rich.console import Console

from .case_importer import prepare_labeling_images
from .case_model import scan_cases, write_all_case_metadata
from .fusion import fuse_case_results
from .paths import CONFIGS_DIR, LABELING_DIR, RAW_DIR, REPORTS_DIR, YOLO_DATASET_DIR
from .reporting import write_case_report_json, write_case_report_md
from .yolo_config import create_yolo_yaml

console = Console()


def cmd_prepare(args: argparse.Namespace) -> int:
    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    count = prepare_labeling_images(raw_dir, out_dir)
    console.print(f"[green]Copied {count} images[/green] to {out_dir}")
    return 0


def cmd_yolo_yaml(args: argparse.Namespace) -> int:
    path = create_yolo_yaml(Path(args.labels), Path(args.out), Path(args.dataset_root))
    console.print(f"[green]YOLO yaml written:[/green] {path}")
    return 0


def cmd_init_dirs(args: argparse.Namespace) -> int:
    dirs = [
        RAW_DIR,
        LABELING_DIR / "images",
        YOLO_DATASET_DIR / "images" / "train",
        YOLO_DATASET_DIR / "images" / "val",
        YOLO_DATASET_DIR / "labels" / "train",
        YOLO_DATASET_DIR / "labels" / "val",
        REPORTS_DIR,
    ]
    for folder in dirs:
        folder.mkdir(parents=True, exist_ok=True)
        console.print(f"created: {folder}")
    return 0


def cmd_scan_cases(args: argparse.Namespace) -> int:
    cases = scan_cases(Path(args.raw))
    count = write_all_case_metadata(cases, Path(args.out))
    console.print(f"[green]Scanned {len(cases)} cases[/green]")
    console.print(f"[green]Wrote {count} metadata files[/green] to {args.out}")
    for case in cases:
        console.print(f"- {case.case_id}: {len(case.images)} images, plate={case.plate}")
    return 0


def cmd_mock_report(args: argparse.Namespace) -> int:
    cases = scan_cases(Path(args.raw))
    for case in cases:
        fusion = fuse_case_results(case.case_id, detections=[], ocr_results=[])
        json_path = write_case_report_json(case, fusion, Path(args.out))
        md_path = write_case_report_md(case, fusion, Path(args.out))
        console.print(f"[green]Report written:[/green] {md_path}")
        console.print(f"[dim]{json_path}[/dim]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="steelcoil", description="Steel coil inspection project CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-dirs", help="Create project data folders")
    p.set_defaults(func=cmd_init_dirs)

    p = sub.add_parser("prepare", help="Copy raw case images into labeling folder")
    p.add_argument("--raw", default=str(RAW_DIR))
    p.add_argument("--out", default=str(LABELING_DIR / "images"))
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("yolo-yaml", help="Create YOLO dataset yaml")
    p.add_argument("--labels", default=str(CONFIGS_DIR / "labels.yaml"))
    p.add_argument("--out", default=str(YOLO_DATASET_DIR / "steel_coil.yaml"))
    p.add_argument("--dataset-root", default=str(YOLO_DATASET_DIR))
    p.set_defaults(func=cmd_yolo_yaml)

    p = sub.add_parser("scan-cases", help="Scan raw case folders and write metadata.json per case")
    p.add_argument("--raw", default=str(RAW_DIR))
    p.add_argument("--out", default=str(REPORTS_DIR))
    p.set_defaults(func=cmd_scan_cases)

    p = sub.add_parser("mock-report", help="Create empty Case First reports for current raw cases")
    p.add_argument("--raw", default=str(RAW_DIR))
    p.add_argument("--out", default=str(REPORTS_DIR))
    p.set_defaults(func=cmd_mock_report)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
