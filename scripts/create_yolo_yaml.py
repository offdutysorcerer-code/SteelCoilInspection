import argparse
import yaml
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Create YOLO dataset yaml from configs/labels.yaml.")
    parser.add_argument("--labels", default="configs/labels.yaml")
    parser.add_argument("--out", default="data/yolo/steel_coil.yaml")
    args = parser.parse_args()

    labels_path = Path(args.labels)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with labels_path.open("r", encoding="utf-8") as f:
        labels_config = yaml.safe_load(f)

    names = labels_config["names"]

    dataset_yaml = {
        "path": str(Path("data/yolo").resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": names,
    }

    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(dataset_yaml, f, allow_unicode=True, sort_keys=False)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
