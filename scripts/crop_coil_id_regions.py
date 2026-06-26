import argparse
from pathlib import Path
import cv2
from ultralytics import YOLO

COIL_ID_CLASS = 1
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def collect_images(source: Path):
    if source.is_file():
        return [source]
    return sorted([p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXTS])


def main():
    parser = argparse.ArgumentParser(description='Crop coil_id_text regions for OCR.')
    parser.add_argument('--weights', required=True)
    parser.add_argument('--source', default='data/raw')
    parser.add_argument('--out', default='runs/coil_id_crops')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--padding', type=int, default=12)
    args = parser.parse_args()

    model = YOLO(args.weights)
    source = Path(args.source)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    images = collect_images(source)
    crop_count = 0

    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        results = model.predict(source=str(img_path), conf=args.conf, verbose=False)
        if not results:
            continue
        r = results[0]
        if r.boxes is None:
            continue
        for idx, box in enumerate(r.boxes):
            cls_id = int(box.cls.item())
            if cls_id != COIL_ID_CLASS:
                continue
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            x1 = max(0, x1 - args.padding)
            y1 = max(0, y1 - args.padding)
            x2 = min(w, x2 + args.padding)
            y2 = min(h, y2 + args.padding)
            crop = img[y1:y2, x1:x2]
            case_name = img_path.parent.name
            target_dir = out_dir / case_name
            target_dir.mkdir(parents=True, exist_ok=True)
            out_path = target_dir / f'{img_path.stem}_coil_id_{idx}.jpg'
            cv2.imwrite(str(out_path), crop)
            crop_count += 1

    print(f'Cropped {crop_count} coil_id_text regions to {out_dir}')


if __name__ == '__main__':
    main()
