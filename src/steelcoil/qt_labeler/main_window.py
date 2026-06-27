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
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from .image_canvas import ImageCanvas
from .inference import InferenceEngine
from .models import Box, ImageAnnotation, load_case_annotation, save_case_annotation
from .yolo_export import LABELS, export_case_to_yolo
from ..case_model import parse_case_id
from ..paths import IMAGE_EXTENSIONS


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Steel Coil Case Labeler - v0.2 UI Tabs")
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
        self.thumbnail_list.setIconSize(QSize(220, 124))
        self.thumbnail_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.thumbnail_list.currentRowChanged.connect(self.on_image_selected)

        self.box_list = QListWidget()
        self.box_list.currentRowChanged.connect(self.on_box_list_selected)

        self.coil_tree = QListWidget()
        self.coil_tree.currentRowChanged.connect(self.on_coil_tree_selected)

        self.label_combo = QComboBox()
        self.label_combo.addItems(LABELS)
        self.label_combo.currentTextChanged.connect(self.on_label_changed)

        self.track_combo = QComboBox()
        self.track_combo.currentIndexChanged.connect(self.on_track_changed)
        self.new_coil_button = QPushButton("新增 Coil / 指派給選取框")
        self.new_coil_button.clicked.connect(self.create_or_assign_new_coil)

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
        self.clear_pred_button = QPushButton("清空預測框")
        self.clear_pred_button.clicked.connect(self.clear_predictions)

        # AI Toggle Button
        self.ai_toggle_button = QPushButton("AI 推論：關閉")
        self.ai_toggle_button.clicked.connect(self.toggle_ai_inference)
        self.ai_toggle_button.setStyleSheet("color: red; font-weight: bold;")

        self.canvas = ImageCanvas()
        self.canvas.annotation_changed.connect(self.on_annotation_changed)
        self.canvas.selection_changed.connect(self.on_selection_changed)

        # AI Inference Engine
        self.inference_engine = InferenceEngine(
            "runs/detect/runs/detect/steel_coil-2/weights/best.pt"
        )
        self.is_ai_enabled = False  # Start with AI disabled

        label_box = QGroupBox("標籤快捷鍵")
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("1 coil\n2 coil_id_text\n3 rubber_pad\n4 wood\n5 chain\n6 strap\n7 truck\n8 trailer"))
        label_box.setLayout(label_layout)

        case_tab = QWidget()
        case_tab_layout = QVBoxLayout()
        case_tab_layout.addWidget(self.case_stats_label)
        case_tab_layout.addWidget(self.image_stats_label)
        case_tab_layout.addWidget(label_box)
        case_tab_layout.addStretch(1)
        case_tab.setLayout(case_tab_layout)

        coil_tab = QWidget()
        coil_tab_layout = QVBoxLayout()
        coil_tab_layout.addWidget(QLabel("Coil Tree"))
        coil_tab_layout.addWidget(self.coil_tree, 1)
        coil_tab.setLayout(coil_tab_layout)

        box_tab = QWidget()
        box_tab_layout = QVBoxLayout()
        box_tab_layout.addWidget(QLabel("目前圖片標註框"))
        box_tab_layout.addWidget(self.box_list, 1)
        box_tab.setLayout(box_tab_layout)

        camera_tab = QWidget()
        camera_tab_layout = QVBoxLayout()
        camera_tab_layout.addWidget(QLabel("Camera / 圖片"))
        camera_tab_layout.addWidget(self.thumbnail_list, 1)
        camera_tab.setLayout(camera_tab_layout)

        self.left_tabs = QTabWidget()
        self.left_tabs.addTab(case_tab, "Case")
        self.left_tabs.addTab(coil_tab, "Coils")
        self.left_tabs.addTab(box_tab, "Boxes")
        self.left_tabs.addTab(camera_tab, "Camera")
        self.left_tabs.setCurrentWidget(camera_tab)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.case_label)
        left_layout.addWidget(QLabel("目前標籤"))
        left_layout.addWidget(self.label_combo)
        left_layout.addWidget(self.selected_label)
        left_layout.addWidget(QLabel("Track ID / Parent Coil"))
        left_layout.addWidget(self.track_combo)
        left_layout.addWidget(self.new_coil_button)
        left_layout.addWidget(self.left_tabs, 1)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.next_unlabeled_button)
        nav_layout.addWidget(self.undo_button)
        left_layout.addLayout(nav_layout)

        edit_layout = QHBoxLayout()
        edit_layout.addWidget(self.copy_button)
        edit_layout.addWidget(self.paste_button)
        left_layout.addLayout(edit_layout)

        io_layout = QHBoxLayout()
        io_layout.addWidget(self.save_button)
        io_layout.addWidget(self.export_button)
        io_layout.addWidget(self.clear_pred_button)
        io_layout.addWidget(self.ai_toggle_button)
        left_layout.addLayout(io_layout)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(380)

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
        self.refresh_coil_tree()
        self.refresh_track_combo()
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
            camera = image_path.stem.split("_")[-1]
            item = QListWidgetItem(f"{prefix} {camera}｜框數：{count}")
            item.setToolTip(image_path.name)
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                item.setIcon(pixmap.scaled(220, 124, Qt.AspectRatioMode.KeepAspectRatio))
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
                track_text = self.track_text_for_box(box)
                item = QListWidgetItem(
                    f"{index}. {box.label} {track_text}  x={box.x:.0f}, y={box.y:.0f}, w={box.width:.0f}, h={box.height:.0f}"
                )
                item.setData(Qt.ItemDataRole.UserRole, box.id)
                self.box_list.addItem(item)
        self.box_list.blockSignals(False)

    def track_text_for_box(self, box: Box) -> str:
        if not self.annotation:
            return ""
        track_id = box.track_id if box.label == "coil" else box.parent_track_id
        coil = self.annotation.coil_by_track_id(track_id)
        if coil:
            return f"[{coil.display_name}]"
        if track_id:
            return f"[{track_id}]"
        return "[未指派]" if box.label in ("coil", "coil_id_text") else ""

    def refresh_track_combo(self) -> None:
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        self.track_combo.addItem("未指派", "")
        if self.annotation:
            for coil in self.annotation.coils:
                self.track_combo.addItem(coil.display_name, coil.track_id)
        selected = self.canvas.get_selected_box()
        selected_track = None
        if selected:
            selected_track = selected.track_id if selected.label == "coil" else selected.parent_track_id
        for index in range(self.track_combo.count()):
            if self.track_combo.itemData(index) == (selected_track or ""):
                self.track_combo.setCurrentIndex(index)
                break
        self.track_combo.blockSignals(False)

    def refresh_coil_tree(self) -> None:
        self.coil_tree.blockSignals(True)
        self.coil_tree.clear()
        if self.annotation:
            for coil in self.annotation.coils:
                cameras = []
                has_text = False
                for image_path, image_ann in self.annotation.annotations.items():
                    camera_has_coil = False
                    for box in image_ann.boxes:
                        if box.track_id == coil.track_id or box.parent_track_id == coil.track_id:
                            camera_has_coil = True
                        if box.label == "coil_id_text" and box.parent_track_id == coil.track_id:
                            has_text = True
                    if camera_has_coil:
                        cameras.append(image_ann.camera or Path(image_path).stem)
                suffix = "；文字✓" if has_text else "；文字○"
                item = QListWidgetItem(f"{coil.display_name} ({', '.join(cameras) if cameras else '尚無 camera'}{suffix})")
                item.setData(Qt.ItemDataRole.UserRole, coil.track_id)
                self.coil_tree.addItem(item)
        self.coil_tree.blockSignals(False)

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

    def on_coil_tree_selected(self, row: int) -> None:
        if row < 0 or not self.annotation:
            return
        item = self.coil_tree.item(row)
        if not item:
            return
        track_id = item.data(Qt.ItemDataRole.UserRole)
        if not track_id:
            return
        for image_index, image_path in enumerate(self.image_paths):
            image_ann = self.annotation.get_image_annotation(image_path)
            for box in image_ann.boxes:
                if box.track_id == track_id or box.parent_track_id == track_id:
                    self.thumbnail_list.setCurrentRow(image_index)
                    self.canvas.selected_box_id = box.id
                    self.canvas.selection_changed.emit(box)
                    self.canvas.update()
                    return

    def on_image_selected(self, row: int) -> None:
        if self.is_refreshing_ui:
            return
        if row < 0 or row >= len(self.image_paths) or not self.annotation:
            return
        self.current_image = self.image_paths[row]
        image_ann = self.annotation.get_image_annotation(self.current_image)
        self.canvas.set_image(self.current_image, image_ann)
        
        # Trigger AI Inference if enabled
        if self.is_ai_enabled and self.inference_engine.is_loaded:
            predictions = self.inference_engine.predict(self.current_image)
            self.canvas.set_predictions(predictions)
            self.status_label.setText(f"AI 推論完成：{len(predictions)} 個預測框")
        else:
            self.canvas.set_predictions([])

        self.refresh_box_list()
        self.refresh_coil_tree()
        self.refresh_track_combo()
        self.update_image_stats()
        self.update_case_stats()

    def on_label_changed(self, label: str) -> None:
        self.canvas.set_label(label)
        self.refresh_dynamic_panels()

    def on_annotation_changed(self) -> None:
        # 停用自動指派，維持使用者標註意圖
        # self.assign_default_track_for_selected_box()
        self.push_history()
        self.save_annotations()
        self.refresh_dynamic_panels()

    def on_track_changed(self) -> None:
        if not self.annotation:
            return
        box = self.canvas.get_selected_box()
        if not box:
            return
        track_id = self.track_combo.currentData() or None
        if box.label == "coil":
            box.track_id = track_id
        elif box.label == "coil_id_text":
            box.parent_track_id = track_id
        else:
            return
        self.save_annotations()
        self.refresh_dynamic_panels()
        self.canvas.update()

    def create_or_assign_new_coil(self) -> None:
        if not self.annotation:
            return
        coil = self.annotation.create_coil()
        box = self.canvas.get_selected_box()
        if box:
            if box.label == "coil":
                box.track_id = coil.track_id
            elif box.label == "coil_id_text":
                box.parent_track_id = coil.track_id
        self.save_annotations()
        self.refresh_dynamic_panels()
        self.canvas.update()

    def assign_default_track_for_selected_box(self) -> None:
        if not self.annotation or not self.current_image:
            return
        box = self.canvas.get_selected_box()
        if not box:
            return
        if box.label == "coil" and not box.track_id:
            coil = self.annotation.create_coil()
            box.track_id = coil.track_id
        elif box.label == "coil_id_text" and not box.parent_track_id:
            parent = self.find_containing_coil(box)
            if parent and parent.track_id:
                box.parent_track_id = parent.track_id

    def find_containing_coil(self, child: Box) -> Box | None:
        if not self.annotation or not self.current_image:
            return None
        image_ann = self.annotation.get_image_annotation(self.current_image)
        child_center_x = child.x + child.width / 2
        child_center_y = child.y + child.height / 2
        for candidate in image_ann.boxes:
            if candidate.id == child.id or candidate.label != "coil":
                continue
            if (
                candidate.x <= child_center_x <= candidate.x + candidate.width
                and candidate.y <= child_center_y <= candidate.y + candidate.height
            ):
                return candidate
        return None

    def on_selection_changed(self, box) -> None:
        if box is None:
            self.selected_label.setText("選取框：無")
            self.box_list.blockSignals(True)
            self.box_list.clearSelection()
            self.box_list.blockSignals(False)
            self.refresh_track_combo()
            return
        self.selected_label.setText(f"選取框：{box.label} {self.track_text_for_box(box)} ({box.width:.0f} x {box.height:.0f})")
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
        self.refresh_track_combo()

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
        coil_count = len(self.annotation.coils)
        self.case_stats_label.setText(
            f"Case 完成度：{labeled_images}/{len(self.image_paths)} 張｜Coil 數：{coil_count}\n" + "\n".join(label_lines)
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

    def clear_predictions(self) -> None:
        self.canvas.clear_predictions()
        self.status_label.setText("已清空所有預測框")

    def toggle_ai_inference(self) -> None:
        self.is_ai_enabled = not self.is_ai_enabled
        if self.is_ai_enabled:
            self.ai_toggle_button.setText("AI 推論：開啟")
            self.ai_toggle_button.setStyleSheet("color: green; font-weight: bold;")
            self.status_label.setText("AI 推論已開啟")
        else:
            self.ai_toggle_button.setText("AI 推論：關閉")
            self.ai_toggle_button.setStyleSheet("color: red; font-weight: bold;")
            self.canvas.set_predictions([])
            self.status_label.setText("AI 推論已關閉")
        
        # Refresh current image to apply changes
        if self.current_image and self.annotation:
            self.on_image_selected(self.image_paths.index(self.current_image))

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
