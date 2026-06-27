from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QImage, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QWidget

from .models import Box, ImageAnnotation

LABEL_COLORS = {
    "coil": Qt.GlobalColor.red,
    "coil_id_text": Qt.GlobalColor.blue,
    "rubber_pad": Qt.GlobalColor.black,
    "wood": Qt.GlobalColor.darkRed,
    "chain": Qt.GlobalColor.darkYellow,
    "strap": Qt.GlobalColor.green,
    "truck": Qt.GlobalColor.cyan,
    "trailer": Qt.GlobalColor.magenta,
    # Legacy labels from early MVP builds.
    "wood_block": Qt.GlobalColor.darkRed,
    "tarp": Qt.GlobalColor.cyan,
}

HANDLE_SIZE = 9
MIN_BOX_SIZE = 3.0


class ImageCanvas(QWidget):
    annotation_changed = Signal()
    selection_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(800, 600)
        self.image_path: Path | None = None
        self.pixmap: QPixmap | None = None
        self.annotation: ImageAnnotation | None = None
        self.current_label = "coil"
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self.drag_start: QPointF | None = None
        self.drag_current: QPointF | None = None
        self.pan_start: QPointF | None = None
        self.pan_origin: QPointF | None = None
        self.pending_select_box_id: str | None = None
        self.selected_box_id: str | None = None
        self.resize_handle: str | None = None
        self.resize_original: QRectF | None = None
        self.prediction_boxes: list[dict] = []  # Stores AI prediction results
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_image(self, image_path: Path, annotation: ImageAnnotation) -> None:
        self.image_path = Path(image_path)
        self.annotation = annotation
        image = QImage(str(image_path))
        self.pixmap = QPixmap.fromImage(image)
        self.selected_box_id = None
        self.pending_select_box_id = None
        self.resize_handle = None
        self.resize_original = None
        self.fit_to_window()
        self.selection_changed.emit(None)
        self.update()

    def set_label(self, label: str) -> None:
        self.current_label = label
        selected = self.get_selected_box()
        if selected:
            selected.label = label
            self.annotation_changed.emit()
        self.update()

    def set_predictions(self, predictions: list[dict]) -> None:
        """Update the prediction boxes and refresh the canvas."""
        self.prediction_boxes = predictions
        self.update()

    def accept_prediction(self, pred: dict) -> bool:
        """Convert a prediction box into a formal annotation box."""
        if not self.annotation:
            return False
        
        # Create a new Box from prediction data
        new_box = Box.create(
            pred["label"],
            pred["x"],
            pred["y"],
            pred["width"],
            pred["height"]
        )
        
        # Add to annotation
        self.annotation.boxes.append(new_box)
        
        # Remove from predictions to avoid duplicates
        self.prediction_boxes = [p for p in self.prediction_boxes if p != pred]
        
        # Select the new box
        self.selected_box_id = new_box.id
        self.selection_changed.emit(new_box)
        self.annotation_changed.emit()
        self.update()
        return True

    def clear_predictions(self) -> None:
        """Clear all prediction boxes."""
        self.prediction_boxes = []
        self.update()

    def get_selected_box(self) -> Box | None:
        if not self.annotation or not self.selected_box_id:
            return None
        for box in self.annotation.boxes:
            if box.id == self.selected_box_id:
                return box
        return None

    def fit_to_window(self) -> None:
        if not self.pixmap or self.pixmap.isNull():
            return
        w_scale = self.width() / self.pixmap.width()
        h_scale = self.height() / self.pixmap.height()
        self.scale = min(w_scale, h_scale) * 0.95
        draw_w = self.pixmap.width() * self.scale
        draw_h = self.pixmap.height() * self.scale
        self.offset = QPointF((self.width() - draw_w) / 2, (self.height() - draw_h) / 2)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)

    def image_to_screen(self, rect: QRectF) -> QRectF:
        return QRectF(
            self.offset.x() + rect.x() * self.scale,
            self.offset.y() + rect.y() * self.scale,
            rect.width() * self.scale,
            rect.height() * self.scale,
        )

    def screen_to_image(self, point: QPointF) -> QPointF:
        return QPointF((point.x() - self.offset.x()) / self.scale, (point.y() - self.offset.y()) / self.scale)

    def clamp_image_rect(self, rect: QRectF) -> QRectF:
        if not self.pixmap:
            return rect
        x1 = max(0.0, min(rect.left(), rect.right()))
        y1 = max(0.0, min(rect.top(), rect.bottom()))
        x2 = min(float(self.pixmap.width()), max(rect.left(), rect.right()))
        y2 = min(float(self.pixmap.height()), max(rect.top(), rect.bottom()))
        return QRectF(x1, y1, max(MIN_BOX_SIZE, x2 - x1), max(MIN_BOX_SIZE, y2 - y1))

    def box_rect(self, box: Box) -> QRectF:
        return QRectF(box.x, box.y, box.width, box.height)

    def apply_rect_to_box(self, box: Box, rect: QRectF) -> None:
        rect = self.clamp_image_rect(rect.normalized())
        box.x = rect.x()
        box.y = rect.y()
        box.width = rect.width()
        box.height = rect.height()

    def handle_rects_for_box(self, box: Box) -> dict[str, QRectF]:
        rect = self.image_to_screen(self.box_rect(box))
        half = HANDLE_SIZE / 2
        points = {
            "tl": rect.topLeft(),
            "tr": rect.topRight(),
            "bl": rect.bottomLeft(),
            "br": rect.bottomRight(),
        }
        return {
            name: QRectF(point.x() - half, point.y() - half, HANDLE_SIZE, HANDLE_SIZE)
            for name, point in points.items()
        }

    def handle_at(self, point: QPointF) -> str | None:
        selected = self.get_selected_box()
        if not selected:
            return None
        for name, rect in self.handle_rects_for_box(selected).items():
            if rect.contains(point):
                return name
        return None

    def box_at_prediction(self, point: QPointF) -> dict | None:
        """Check if a point is inside any prediction box."""
        if not self.prediction_boxes:
            return None
        image_point = self.screen_to_image(point)
        for pred in self.prediction_boxes:
            rect = QRectF(pred["x"], pred["y"], pred["width"], pred["height"])
            if rect.contains(image_point):
                return pred
        return None

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.darkGray)

        if not self.pixmap or self.pixmap.isNull():
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No image loaded")
            return

        target = QRectF(self.offset.x(), self.offset.y(), self.pixmap.width() * self.scale, self.pixmap.height() * self.scale)
        painter.drawPixmap(target, self.pixmap, QRectF(self.pixmap.rect()))

        if self.annotation:
            # Draw prediction boxes (green dashed lines)
            if self.prediction_boxes:
                for pred in self.prediction_boxes:
                    rect = QRectF(pred["x"], pred["y"], pred["width"], pred["height"])
                    screen_rect = self.image_to_screen(rect)
                    painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine))
                    painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                    painter.drawRect(screen_rect)
                    
                    # Draw a small indicator circle in the center to show it's clickable
                    center = screen_rect.center()
                    painter.setPen(QPen(Qt.GlobalColor.white, 2))
                    painter.setBrush(QBrush(Qt.GlobalColor.green))
                    painter.drawEllipse(center, 4, 4)

                    # Draw label
                    painter.drawText(screen_rect.topLeft() + QPointF(4, -4), f"{pred['label']} {pred['confidence']:.2f}")

            for box in self.annotation.boxes:
                color = LABEL_COLORS.get(box.label, Qt.GlobalColor.yellow)
                pen_width = 4 if box.id == self.selected_box_id else 2
                painter.setPen(QPen(color, pen_width))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                screen_rect = self.image_to_screen(self.box_rect(box))
                painter.drawRect(screen_rect)
                painter.drawText(screen_rect.topLeft() + QPointF(4, -4), box.label)

                if box.id == self.selected_box_id:
                    painter.setPen(QPen(Qt.GlobalColor.white, 1))
                    painter.setBrush(QBrush(color))
                    for handle_rect in self.handle_rects_for_box(box).values():
                        painter.drawRect(handle_rect)

        if self.drag_start and self.drag_current and not self.resize_handle:
            color = LABEL_COLORS.get(self.current_label, Qt.GlobalColor.yellow)
            painter.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRect(QRectF(self.drag_start, self.drag_current).normalized())

    def box_at(self, point: QPointF) -> Box | None:
        if not self.annotation:
            return None
        image_point = self.screen_to_image(point)
        candidates = []
        for index, box in enumerate(self.annotation.boxes):
            rect = self.box_rect(box)
            if rect.contains(image_point):
                area = max(0.0, rect.width() * rect.height())
                # Prefer the smallest containing box so nested labels such as
                # coil_id_text inside coil can be selected by direct click.
                # For same-sized overlaps, prefer the later-created box.
                candidates.append((area, -index, box))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    def box_by_id(self, box_id: str | None) -> Box | None:
        if not box_id or not self.annotation:
            return None
        for box in self.annotation.boxes:
            if box.id == box_id:
                return box
        return None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.setFocus()
        if not self.pixmap:
            return

        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.pan_start = QPointF(event.position())
            self.pan_origin = QPointF(self.offset)
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.delete_box_at(event.position())
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked on a prediction box
            pred = self.box_at_prediction(event.position())
            if pred:
                self.accept_prediction(pred)
                return

            handle = self.handle_at(event.position())
            selected = self.get_selected_box()
            if handle and selected:
                self.resize_handle = handle
                self.resize_original = self.box_rect(selected)
                self.drag_current = QPointF(event.position())
                return

            # Click selects. Drag creates a new box even when starting inside a larger box.
            # This supports nested labels, e.g. coil_id_text inside coil.
            box = self.box_at(event.position())
            self.pending_select_box_id = box.id if box else None
            self.drag_start = QPointF(event.position())
            self.drag_current = QPointF(event.position())
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self.pan_start and self.pan_origin:
            delta = QPointF(event.position()) - self.pan_start
            self.offset = self.pan_origin + delta
            self.update()
            return

        if self.resize_handle:
            self.resize_selected_box(event.position())
            self.update()
            return

        if self.drag_start:
            self.drag_current = QPointF(event.position())
            self.update()

    def resize_selected_box(self, screen_point: QPointF) -> None:
        box = self.get_selected_box()
        if not box or not self.resize_original:
            return
        p = self.screen_to_image(screen_point)
        r = QRectF(self.resize_original)
        if self.resize_handle == "tl":
            r.setTopLeft(p)
        elif self.resize_handle == "tr":
            r.setTopRight(p)
        elif self.resize_handle == "bl":
            r.setBottomLeft(p)
        elif self.resize_handle == "br":
            r.setBottomRight(p)
        self.apply_rect_to_box(box, r)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.MiddleButton:
            self.pan_start = None
            self.pan_origin = None
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self.resize_handle:
            self.resize_handle = None
            self.resize_original = None
            self.drag_current = None
            self.annotation_changed.emit()
            self.update()
            return

        if not self.drag_start or not self.drag_current:
            return
        if not self.annotation or not self.pixmap:
            return

        screen_rect = QRectF(self.drag_start, self.drag_current).normalized()
        is_click = screen_rect.width() < 5 and screen_rect.height() < 5

        if is_click:
            selected = self.box_by_id(self.pending_select_box_id)
            self.selected_box_id = selected.id if selected else None
            self.selection_changed.emit(selected)
            self.drag_start = None
            self.drag_current = None
            self.pending_select_box_id = None
            self.update()
            return

        p1 = self.screen_to_image(screen_rect.topLeft())
        p2 = self.screen_to_image(screen_rect.bottomRight())
        image_rect = self.clamp_image_rect(QRectF(p1, p2).normalized())
        box = Box.create(self.current_label, image_rect.x(), image_rect.y(), image_rect.width(), image_rect.height())
        self.annotation.boxes.append(box)
        self.selected_box_id = box.id
        self.drag_start = None
        self.drag_current = None
        self.pending_select_box_id = None
        self.selection_changed.emit(box)
        self.annotation_changed.emit()
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if not self.pixmap:
            return
        mouse_pos = QPointF(event.position())
        before = self.screen_to_image(mouse_pos)
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale = max(0.05, min(8.0, self.scale * factor))
        after_screen = QPointF(before.x() * self.scale + self.offset.x(), before.y() * self.scale + self.offset.y())
        self.offset += mouse_pos - after_screen
        self.update()

    def delete_selected_box(self) -> None:
        if not self.annotation or not self.selected_box_id:
            return
        self.annotation.boxes = [box for box in self.annotation.boxes if box.id != self.selected_box_id]
        self.selected_box_id = None
        self.selection_changed.emit(None)
        self.annotation_changed.emit()
        self.update()

    def delete_box_at(self, point: QPointF) -> None:
        box = self.box_at(point)
        if not box or not self.annotation:
            return
        self.annotation.boxes = [b for b in self.annotation.boxes if b.id != box.id]
        if self.selected_box_id == box.id:
            self.selected_box_id = None
            self.selection_changed.emit(None)
        self.annotation_changed.emit()
        self.update()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected_box()
        elif event.key() == Qt.Key.Key_F:
            self.fit_to_window()
            self.update()
        else:
            super().keyPressEvent(event)
