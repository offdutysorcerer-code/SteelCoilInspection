import argparse
import random
import shutil
import sys
from pathlib import Path

# Add project root to path to import src modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from steelcoil.qt_labeler.models import load_case_annotation

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def collect_images(raw_dir: Path):
    return sorted([p for p in raw_dir.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXTS])

def ensure_dirs(out_dir: Path):
    for sub in ['images/train', 'images/val', 'labels/train', 'labels/val']:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

def unique_name(raw_root: Path, image_path: Path):
    rel = image_path.relative_to(raw_root)
    parts = list(rel.parts)
    return '__'.join(parts)

def convert_json_to_yolo(case_dir: Path, out_labels_dir: Path):
    """Convert .steelcoil_annotations.json to YOLO format in out_labels_dir."""
    json_path = case_dir / '.steelcoil_annotations.json'
    if not json_path.exists():
        return []

    ann = load_case_annotation(case_dir)
    converted_files = []
    
    for image_path_text, image_ann in ann.annotations.items():
        image_path = Path(image_path_text)
        if not image_path.exists():
            continue
        
        # Generate YOLO txt filename based on image name
        # e.g., 20220930_095258_KLC9857F_cam01.txt
        stem = image_path.stem
        txt_path = out_labels_dir / f"{stem}.txt"
        
        # Load labels.yaml to map names to IDs
        labels_path = Path(__file__).resolve().parent.parent / "configs" / "labels.yaml"
        if not labels_path.exists():
            print(f"Warning: labels.yaml not found at {labels_path}")
            continue
            
        import yaml
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels_config = yaml.safe_load(f)
        
        names = labels_config.get('names', {})
        # Create reverse map: name -> id
        name_to_id = {v: int(k) for k, v in names.items()}
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            for box in image_ann.boxes:
                # Normalize box to 0-1 range
                # YOLO format: class x_center y_center width height
                # Assuming boxes are in image coordinates. We need image width/height.
                # For simplicity, if width/height is 0 or unknown, we assume normalized coords or skip.
                # However, our boxes are absolute pixels. We need image size.
                # Let's assume we can get it from the image file or it's stored in JSON?
                # Currently JSON doesn't store image size. We have to load the image or assume it's not needed if we normalize later.
                # But YOLO requires relative coords.
                # Let's load image size here.
                try:
                    from PIL import Image
                    img = Image.open(image_path)
                    w, h = img.size
                except:
                    continue # Skip if can't load image
                
                # Normalize
                x_center = (box.x + box.width / 2) / w
                y_center = (box.y + box.height / 2) / h
                width = box.width / w
                height = box.height / h
                
                # Map label
                label_name = box.label
                # Handle legacy aliases
                if label_name == 'wood_block':
                    label_name = 'wood'
                
                class_id = name_to_id.get(label_name)
                if class_id is not None:
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        converted_files.append(txt_path)
        
    return converted_files

def main():
    parser = argparse.ArgumentParser(description='Prepare YOLO dataset from raw annotated folders.')
    parser.add_argument('--raw', default='data/raw', help='Raw image root.')
    parser.add_argument('--out', default='data/yolo', help='YOLO output root.')
    parser.add_argument('--val-ratio', type=float, default=0.2, help='Validation split ratio.')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    ensure_dirs(out_dir)

    # 1. Convert all JSONs to YOLO txt labels in a temporary or parallel structure
    # We will create a mapping: original_image_path -> txt_path
    image_to_txt = {}
    
    # Find all case directories
    case_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and (d / '.steelcoil_annotations.json').exists()]
    
    if not case_dirs:
        print(f"No annotated case directories found in {raw_dir}")
        return

    # Create a temporary labels dir for conversion
    temp_labels_dir = out_dir / 'temp_labels'
    temp_labels_dir.mkdir(exist_ok=True)

    for case_dir in case_dirs:
        converted = convert_json_to_yolo(case_dir, temp_labels_dir)
        for txt in converted:
            # Map original image stem to txt path
            # We need to find the original image path to match it later
            # Since we don't have the path in txt name, let's store mapping in a dict
            # Actually, let's just copy images and txts directly in the next step using the txts generated
            
            # Find corresponding image in case_dir
            stem = txt.stem
            img_path = case_dir / f"{stem}.jpeg" # Assuming jpeg based on previous checks
            if not img_path.exists():
                img_path = case_dir / f"{stem}.jpg"
            if img_path.exists():
                image_to_txt[str(img_path)] = str(txt)

    # 2. Collect images again (now we have txts ready)
    images = collect_images(raw_dir)
    
    random.seed(args.seed)
    random.shuffle(images)

    val_count = max(1, int(len(images) * args.val_ratio)) if len(images) > 1 else 0
    val_set = set(images[:val_count])

    copied = 0
    for img in images:
        split = 'val' if img in val_set else 'train'
        dst_name = unique_name(raw_dir, img)
        dst_img = out_dir / 'images' / split / dst_name
        shutil.copy2(img, dst_img)

        # Try to find txt
        img_str = str(img)
        txt_src = image_to_txt.get(img_str)
        if txt_src:
            txt_path = Path(txt_src)
            dst_label = out_dir / 'labels' / split / Path(dst_name).with_suffix('.txt').name
            shutil.copy2(txt_path, dst_label)
        else:
            # Create empty txt
            dst_label = out_dir / 'labels' / split / Path(dst_name).with_suffix('.txt').name
            dst_label.write_text('', encoding='utf-8')
            
        copied += 1

    # Cleanup temp
    if temp_labels_dir.exists():
        shutil.rmtree(temp_labels_dir)

    print(f'Copied {copied} images to {out_dir}')

if __name__ == '__main__':
    main()
