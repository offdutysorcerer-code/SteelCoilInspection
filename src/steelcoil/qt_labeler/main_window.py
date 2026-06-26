from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from .image_canvas import ImageCanvas
from .models import Box, ImageAnnotation, load_case_annotation, save_case_annotation
from .yolo_export import LABELS, export_case_to_yolo
from ..case_model import parse_case_id
from ..paths import IMAGE_EXTENSIONS


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Steel Coil Case Labeler")
        self.resize(1550, 920)

        self.case_dir: Path | None = None
        self.image_paths: list[Path] = []
        self.annotation = None
        self.current_image: Path | None = None
        self.clipboard_box: Box | None = None
        self.history: list[object] = []
        self.is_restoring = False
        self.is_refreshing_ui = False

        self.case_label = QLabel("尚未載入 Case")
        self.status_label = QLabel(
            "快捷鍵：1~8 切換標籤｜Space/→ 下一張｜← 上一張｜滑輪縮放｜Alt+左鍵或中鍵平移｜Delete 刪除框｜F 適合視窗｜Ctrl+Z 復原｜Ctrl+C/V 複製貼上框"
        )
        self.image_stats_label = QLabel("目前圖片：0 個框")
        self.case_stats_label = QLabel("Case 統計：尚未載入")
        self.selected_label = QLabel("選取框：無")

        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(180, 100))
        self.thumbnail_list.currentRowChanged.connect(self.on_image_selected)

        self.box_list = QListWidget()
        self.box_list.currentRowChanged.connect(self.on_box_list_selected)

        self.label_combo = QComboBox()
        self.label_combo.addItems(LABELS)
        self.label_combo.currentTextChanged.connect(self.on_label_changed)

        self.save_button = QPushButton("儲存")
        self.save_button.clicked.connect(self.save_annotations)
        self.export_button = QPushButton("匯出 YOLO")
        self.export_button.clicked.connect(self.export_yolo)
        self.next_unlabeled_button = QPushButton("下一張未標")
        self.next_unlabeled_button.clicked.connect(self.go_next_unlabeled)
        self.undo_button = QPushButton("復原 Ctrl+Z")
        self.undo_button.clicked.connect(self.undo)
        self.copy_button = QPushButton("複製框 Ctrl+C")
        self.copy_button.clicked.connect(self.copy_selected_box)
        self.paste_button = QPushButton("貼上框 Ctrl+V")
        self.paste_button.clicked.connect(self.paste_box)

        self.canvas = ImageCanvas()
        self.canvas.annotation_changed.connect(self.on_annotation_changed)
        self.canvas.selection_changed.connect(self.on_selection_changed)

        label_box = QGroupBox("標籤快捷鍵")
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("1 coil\n2 coil_id_text\n3 rubber_pad\n4 chain\n5 strap\n6 tarp\n7 wood_block\n8 trailer"))
        label_box.setLayout(label_layout)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.case_label)
        left_layout.addWidget(QLabel("目前標籤"))
        left_layout.addWidget(self.label_combo)
        left_layout.addWidget(label_box)
        left_layout.addWidget(self.case_stats_label)
        left_layout.addWidget(self.image_stats_label)
        left_layout.addWidget(self.selected_label)
        left_layout.addWidget(QLabel("目前圖片標註框"))
        left_layout.addWidget(self.box_list, 1)
        left_layout.addWidget(QLabel("Camera / 圖片"))
        left_layout.addWidget(self.thumbnail_list, 2)
        left_layout.addWidget(self.next_unlabeled_button)
        left_layout.addWidget(self.undo_button)
        left_layout.addWidget(self.copy_button)
        left_layout.addWidget(self.paste_button)
        left_layout.addWidget(self.save_button)
        left_layout.addWidget(self.export_button)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(410)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.canvas, 1)
        right_layout.addWidget(self.status_label)
        right_panel = QWidget()
        right_panel.setLayout(right_layout)

        layout = QHBoxLayout()
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        open_action = QAction("開啟 Case", self)
        open_action.triggered.connect(self.open_case_dialog)
        self.menuBar().addAction(open_action)

    def open_case_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "選擇 Case 資料夾", "D:/AIProjects/A1/SteelCoilInspection/data/raw")
        if folder:
            self.load_case(Path(folder))

    def load_case(self, case_dir: Path) -> None:
        self.case_dir = Path(case_dir)
        self.annotation = load_case_annotation(self.case_dir)
        self.image_paths = sorted(
            p for p in self.case_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        self.history = []
        self.push_history()

        date, time, plate = parse_case_id(self.case_dir.name)
        self.case_label.setText(
            f"Case: {self.case_dir.name}\n日期: {date}\n時間: {time}\n車牌: {plate}\n圖片數: {len(self.image_paths)}"
        )

        self.refresh_thumbnail_list(preserve_row=False)
        self.update_case_stats()
        if self.image_paths:
            self.thumbnail_list.setCurrentRow(0)

    def push_history(self) -> None:
        if self.is_restoring or self.annotation is None:
            return
        self.history.append(deepcopy(self.annotation))
        if len(self.history) > 50:
            self.history.pop(0)

    def undo(self) -> None:
        if self.annotation is None or len(self.history) < 2:
            return
        self.is_restoring = True
        self.history.pop()
        self.annotation = deepcopy(self.history[-1])
        self.is_restoring = False
        if self.current_image:
            image_ann = self.annotation.get_image_annotation(self.current_image)
            self.canvas.set_image(self.current_image, image_ann)
        self.save_annotations()
        self.refresh_dynamic_panels()

    def refresh_dynamic_panels(self) -> None:
        self.refresh_box_list()
        self.update_image_stats()
        self.update_case_stats()
        self.refresh_thumbnail_list(preserve_row=True)

    def refresh_thumbnail_list(self, preserve_row: bool = True) -> None:
        if self.is_refreshing_ui:
            return
        self.is_refreshing_ui = True
        current_row = self.thumbnail_list.currentRow() if preserve_row else -1
        self.thumbnail_list.blockSignals(True)
        self.thumbnail_list.clear()
        for image_path in self.image_paths:
            count = 0
            if self.annotation:
                count = len(self.annotation.get_image_annotation(image_path).boxes)
            prefix = "✓" if count > 0 else "○"
            item = QListWidgetItem(f"{prefix} {image_path.name}\n框數：{count}")
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                item.setIcon(pixmap.scaled(180, 100, Qt.AspectRatioMode.KeepAspectRatio))
            self.thumbnail_list.addItem(item)
        if current_row >= 0 and current_row < self.thumbnail_list.count():
            self.thumbnail_list.setCurrentRow(current_row)
        self.thumbnail_list.blockSignals(False)
        self.is_refreshing_ui = False

    def refresh_box_list(self) -> None:
        self.box_list.blockSignals(True)
        self.box_list.clear()
        if self.annotation and self.current_image:
            image_ann = self.annotation.get_image_annotation(self.current_image)
            for index, box in enumerate(image_ann.boxes, start=1):
                item = QListWidgetItem(f"{index}. {box.label}  x={box.x:.0f}, y={box.y:.0f}, w={box.width:.0f}, h={box.height:.0f}")
                item.setData(Qt.ItemDataRole.UserRole, box.id)
                self.box_list.addItem(item)
        self.box_list.blockSignals(False)

    def on_box_list_selected(self, row: int) -> None:
        if row < 0 or not self.annotation or not self.current_image:
            return
        item = self.box_list.item(row)
        if not item:
            return
        box_id = item.data(Qt.ItemDataRole.UserRole)
        self.canvas.selected_box_id = box_id
        box = self.canvas.get_selected_box()
        self.canvas.selection_changed.emit(box)
        self.canvas.update()

    def on_image_selected(self, row: int) -> None:
        if self.is_refreshing_ui:
            return
        if row < 0 or row >= len(self.image_paths) or not self.annotation:
            return
        self.current_image = self.image_paths[row]
        image_ann = self.annotation.get_image_annotation(self.current_image)
        self.canvas.set_image(self.current_image, image_ann)
        self.refresh_box_list()
        self.update_image_stats()
        self.update_case_stats()

    def on_label_changed(self, label: str) -> None:
        self.canvas.set_label(label)
        self.refresh_dynamic_panels()

    def on_annotation_changed(self) -> None:
        self.push_history()
        self.save_annotations()
        self.refresh_dynamic_panels()

    def on_selection_changed(self, box) -> None:
        if box is None:
            self.selected_label.setText("選取框：無")
            self.box_list.blockSignals(True)
            self.box_list.clearSelection()
            self.box_list.blockSignals(False)
            return
        self.selected_label.setText(f"選取框：{box.label} ({box.width:.0f} x {box.height:.0f})")
        index = LABELS.index(box.label) if box.label in LABELS else -1
        if index >= 0 and self.label_combo.currentIndex() != index:
            self.label_combo.blockSignals(True)
            self.label_combo.setCurrentIndex(index)
            self.label_combo.blockSignals(False)
        self.box_list.blockSignals(True)
        for row in range(self.box_list.count()):
            item = self.box_list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == box.id:
                self.box_list.setCurrentRow(row)
                break
        self.box_list.blockSignals(False)

    def update_image_stats(self) -> None:
        if not self.annotation or not self.current_image:
            self.image_stats_label.setText("目前圖片：0 個框")
            return
        image_ann = self.annotation.get_image_annotation(self.current_image)
        counts = {}
        for box in image_ann.boxes:
            counts[box.label] = counts.get(box.label, 0) + 1
        if counts:
            detail = "｜".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            self.image_stats_label.setText(f"目前圖片：{len(image_ann.boxes)} 個框\n{detail}")
        else:
            self.image_stats_label.setText("目前圖片：0 個框")

    def update_case_stats(self) -> None:
        if not self.annotation:
            self.case_stats_label.setText("Case 統計：尚未載入")
            return
        counts = {label: 0 for label in LABELS}
        labeled_images = 0
        for image_path in self.image_paths:
            image_ann = self.annotation.get_image_annotation(image_path)
            if image_ann.boxes:
                labeled_images += 1
            for box in image_ann.boxes:
                counts[box.label] = counts.get(box.label, 0) + 1
        label_lines = [f"{label}: {count}" for label, count in counts.items() if count > 0]
        if not label_lines:
            label_lines = ["尚無標註"]
        self.case_stats_label.setText(
            f"Case 完成度：{labeled_images}/{len(self.image_paths)} 張\n" + "\n".join(label_lines)
        )

    def save_annotations(self) -> None:
        if self.case_dir and self.annotation:
            save_case_annotation(self.case_dir, self.annotation)

    def copy_selected_box(self) -> None:
        box = self.canvas.get_selected_box()
        if box:
            self.clipboard_box = deepcopy(box)
            self.status_label.setText(f"已複製框：{box.label}")

    def paste_box(self) -> None:
        if not self.clipboard_box or not self.annotation or not self.current_image:
            return
        image_ann: ImageAnnotation = self.annotation.get_image_annotation(self.current_image)
        new_box = Box.create(
            self.clipboard_box.label,
            self.clipboard_box.x + 20,
            self.clipboard_box.y + 20,
            self.clipboard_box.width,
            self.clipboard_box.height,
        )
        image_ann.boxes.append(new_box)
        self.canvas.selected_box_id = new_box.id
        self.canvas.selection_changed.emit(new_box)
        self.on_annotation_changed()
        self.canvas.update()

    def export_yolo(self) -> None:
        if not self.case_dir or not self.annotation:
            QMessageBox.warning(self, "尚未載入", "請先開啟 Case。")
            return
        output = QFileDialog.getExistingDirectory(self, "選擇 YOLO 輸出資料夾", str(Path.cwd() / "data" / "yolo_dataset"))
        if not output:
            return
        self.save_annotations()
        export_case_to_yolo(self.annotation, Path(output))
        QMessageBox.information(self, "完成", f"已匯出 YOLO 到：\n{output}")

    def go_next_unlabeled(self) -> None:
        if not self.annotation or not self.image_paths:
            return
        start = self.thumbnail_list.currentRow()
        total = len(self.image_paths)
        for step in range(1, total + 1):
            row = (start + step) % total
            image_ann = self.annotation.get_image_annotation(self.image_paths[row])
            if len(image_ann.boxes) == 0:
                self.thumbnail_list.setCurrentRow(row)
                return
        QMessageBox.information(self, "完成", "所有圖片至少都有一個標註框。")

    def keyPressEvent(self, event) -> None:  # noqa: N802
        row = self.thumbnail_list.currentRow()
        key_to_label = {
            Qt.Key.Key_1: 0,
            Qt.Key.Key_2: 1,
            Qt.Key.Key_3: 2,
            Qt.Key.Key_4: 3,
            Qt.Key.Key_5: 4,
            Qt.Key.Key_6: 5,
            Qt.Key.Key_7: 6,
            Qt.Key.Key_8: 7,
        }
        if event.key() in key_to_label:
            self.label_combo.setCurrentIndex(key_to_label[event.key()])
        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Space):
            self.thumbnail_list.setCurrentRow(min(row + 1, len(self.image_paths) - 1))
        elif event.key() == Qt.Key.Key_Left:
            self.thumbnail_list.setCurrentRow(max(row - 1, 0))
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.save_annotations()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.undo()
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.copy_selected_box()
        elif event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_box()
        else:
            super().keyPressEvent(event)


def run_app() -> int:
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()
