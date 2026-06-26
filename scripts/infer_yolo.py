import argparse
import csv
from pathlib import Path
from ultralytics import YOLO

CLASS_NAMES = ['coil', 'coil_id_text', 'rubber_pad', 'chain', 'strap', 'tarp', 'wood_block', 'trailer']


def decide_status(counts):
    notes = []
    if counts.get('coil', 0) == 0:
        notes.append('未偵測到鋼捲')
    if counts.get('coil', 0) > 0 and counts.get('coil_id_text', 0) == 0:
        notes.append('未偵測到鋼捲編號區域')
    if counts.get('coil', 0) > 0 and counts.get('strap', 0) + counts.get('chain', 0) == 0:
        notes.append('未偵測到固定物')
    if counts.get('coil', 0) > 0 and counts.get('rubber_pad', 0) + counts.get('wood_block', 0) == 0:
        notes.append('未偵測到墊材或木座')
    return ('REVIEW' if notes else 'PASS'), '; '.join(notes)


def main():
    parser = argparse.ArgumentParser(description='Run YOLO inference and create inspection summary.')
    parser.add_argument('--weights', required=True)
    parser.add_argument('--source', default='data/raw')
    parser.add_argument('--out', default='runs/infer_summary.csv')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--imgsz', type=int, default=1280)
    args = parser.parse_args()

    model = YOLO(args.weights)
    results = model.predict(source=args.source, conf=args.conf, imgsz=args.imgsz, save=True, stream=True)

    rows = []
    for r in results:
        image_path = Path(r.path)
        counts = {name: 0 for name in CLASS_NAMES}
        if r.boxes is not None:
            for cls_id in r.boxes.cls.tolist():
                idx = int(cls_id)
                name = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else str(idx)
                counts[name] = counts.get(name, 0) + 1
        status, notes = decide_status(counts)
        row = {'image': str(image_path), 'status': status, 'notes': notes}
        row.update(counts)
        rows.append(row)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['image', 'status', 'notes'] + CLASS_NAMES
    with out_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'Wrote summary: {out_path}')


if __name__ == '__main__':
    main()
