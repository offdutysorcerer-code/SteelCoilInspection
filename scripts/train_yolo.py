import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description='Train YOLO model for steel coil inspection.')
    parser.add_argument('--data', default='data/yolo/steel_coil.yaml')
    parser.add_argument('--model', default='yolo11n.pt')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=1280)
    parser.add_argument('--batch', type=int, default=4)
    parser.add_argument('--device', default=None, help='Example: 0 for GPU, cpu for CPU.')
    args = parser.parse_args()

    model = YOLO(args.model)
    train_kwargs = {
        'data': args.data,
        'epochs': args.epochs,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'project': 'runs/detect',
        'name': 'steel_coil',
    }
    if args.device is not None:
        train_kwargs['device'] = args.device

    model.train(**train_kwargs)


if __name__ == '__main__':
    main()
