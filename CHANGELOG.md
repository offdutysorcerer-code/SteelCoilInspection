# Changelog

## v0.1.0 - Steel Coil Labeler MVP

### Added

- Case First 標註流程：以一台車次 / 一個 Case 為核心。
- Qt 專屬標註工具。
- cam01～cam14 縮圖瀏覽與大圖切換。
- YOLO Bounding Box 標註。
- 巢狀標註支援：例如在 `coil` 內標 `coil_id_text`。
- 自動儲存 `.steelcoil_annotations.json`。
- YOLO Dataset 匯出。
- 滑鼠滾輪縮放。
- Alt+左鍵 / 中鍵平移。
- 1～8 快捷鍵切換 label。
- Ctrl+Z 復原。
- Ctrl+C / Ctrl+V 複製貼上框。
- Delete / Backspace 刪除選取框。
- Resize Handles：拖曳四角調整框大小。
- 左側 Box 清單與選取功能。
- Case 完成度與 Label 統計。
- 下一張未標圖片導覽。

### Fixed

- 修正開啟 Case 後因縮圖刷新重入造成 UI 卡住。
- 修正 `coil_id_text` 被包含在 `coil` 內時無法新建框的問題。
- 封存 Label Studio 舊流程，改以 Qt 工具作為主流程。

### Notes

- Label Studio legacy files 已封存於 `archive/label_studio_legacy`。
- 下一階段目標：Track ID、多相機同一鋼捲關聯、Case 檢查面板、YOLO AI 預標註。
