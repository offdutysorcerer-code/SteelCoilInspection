"""AI Inference Module for Steel Coil Labeler.

This module handles loading the YOLO model and performing predictions on images.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class InferenceEngine:
    """Handles YOLO model loading and inference."""

    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.model: YOLO | None = None
        self.is_loaded = False
        self.load_model()

    def load_model(self) -> bool:
        """Load the YOLO model from disk."""
        if not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            return False
        
        try:
            logger.info(f"Loading YOLO model from: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            self.is_loaded = True
            logger.info("Model loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_loaded = False
            return False

    def predict(self, image_path: str | Path) -> list[dict]:
        """Run inference on an image and return prediction results.

        Args:
            image_path: Path to the input image.

        Returns:
            A list of dictionaries containing box coordinates, label, and confidence.
            Format: [{'x': float, 'y': float, 'width': float, 'height': float, 'label': str, 'confidence': float}, ...]
        """
        if not self.is_loaded or self.model is None:
            logger.warning("Model not loaded. Cannot predict.")
            return []

        try:
            results = self.model(str(image_path))
            predictions = []
            
            if not results or not results[0]:
                return []

            result = results[0]
            boxes = result.boxes
            
            if boxes is None:
                return []

            # Extract data from the boxes tensor
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy()

            # Map class IDs to label names
            names = result.names

            for i in range(len(xyxy)):
                x1, y1, x2, y2 = xyxy[i]
                conf = confs[i]
                cls_id = int(cls_ids[i])
                label = names.get(cls_id, f"class_{cls_id}")

                # Convert xyxy to x, y, width, height
                x = x1
                y = y1
                w = x2 - x1
                h = y2 - y1

                predictions.append({
                    "x": float(x),
                    "y": float(y),
                    "width": float(w),
                    "height": float(h),
                    "label": label,
                    "confidence": float(conf)
                })

            return predictions

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return []
