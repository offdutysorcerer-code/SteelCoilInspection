import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def collect_images(raw_dir: Path):
    return sorted([p for p in raw_dir.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXTS])


def ensure_dirs(out_dir: Path):
    for sub in ['images/train', 'images/val', 'labels/train', 'labels/val']:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def label_for_image(image_path: Path):
    return image_path.with_suffix('.txt')


def unique_name(raw_root: Path, image_path: Path):
    rel = image_path.relative_to(raw_root)
    parts = list(rel.parts)
    return '__'.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Prepare YOLO dataset from raw annotated folders.')
    parser.add_argument('--raw', default='data/raw', help='Raw image root. YOLO txt labels may sit beside images.')
    parser.add_argument('--out', default='data/yolo', help='YOLO output root.')
    parser.add_argument('--val-ratio', type=float, default=0.2, help='Validation split ratio.')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    ensure_dirs(out_dir)

    images = collect_images(raw_dir)
    if not images:
        print(f'No images found under {raw_dir}')
        return

    random.seed(args.seed)
    random.shuffle(images)

    val_count = max(1, int(len(images) * args.val_ratio)) if len(images) > 1 else 0
    val_set = set(images[:val_count])

    copied = 0
    missing_labels = []

    for img in images:
        split = 'val' if img in val_set else 'train'
        dst_name = unique_name(raw_dir, img)
        dst_img = out_dir / 'images' / split / dst_name
        shutil.copy2(img, dst_img)

        src_label = label_for_image(img)
        dst_label = out_dir / 'labels' / split / Path(dst_name).with_suffix('.txt').name
        if src_label.exists():
            shutil.copy2(src_label, dst_label)
        else:
            dst_label.write_text('', encoding='utf-8')
            missing_labels.append(str(img))
        copied += 1

    print(f'Copied {copied} images to {out_dir}')
    if missing_labels:
        print(f'Warning: {len(missing_labels)} images had no YOLO label txt. Empty labels were created.')


if __name__ == '__main__':
    main()
