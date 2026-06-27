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

## v0.2.0-dev - Case Data Model + Track ID

### Added

- 新增 annotation schema v2：`schema_version`、case metadata、`coils[]`、`images[]`。
- 新增 `Coil` data model，支援 `track_id` 與 `display_name`。
- `Box` 新增 `track_id` 與 `parent_track_id`，用於 coil box 與 `coil_id_text` 的歸屬關係。
- Qt Labeler 左側新增 Coil Tree，可顯示每顆 Coil 出現的 camera 與是否已有 `coil_id_text`。
- 選取 `coil` 或 `coil_id_text` 後，可透過 Track ID 下拉選單指派 / 清除歸屬。
- 新增「新增 Coil / 指派給選取框」按鈕。
- 新畫 `coil` box 時會自動建立新的 Coil Track ID。
- 新畫 `coil_id_text` 時，若中心點落在某個 coil box 內，會自動掛到該 coil 的 Track ID。

### Changed

- `.steelcoil_annotations.json` 儲存格式改為 schema v2，但仍可讀取 legacy v1 格式並自動 migration 到記憶體模型。
- YOLO 匯出維持只使用 `label + bbox + image`，不輸出 Track ID。
- YOLO 匯出改為略過沒有有效標註列的圖片。
- Label 清單對齊 roadmap：`coil`, `coil_id_text`, `rubber_pad`, `wood`, `chain`, `strap`, `truck`, `trailer`。

### Compatibility

- 舊版 `wood_block` 於 YOLO 匯出時會 alias 成 `wood`。

### Fixed

- 左側工具列改為分頁式面板：Case、Coils、Boxes、Camera，避免 Coil Tree、Box List、Camera 縮圖全部擠在同一欄。
- 預設開啟 Camera 分頁，讓縮圖選圖區域更大、更容易操作。
- 改善巢狀框點選邏輯：滑鼠點擊同時落在多個框內時，優先選取面積較小的內層框，例如 `coil` 內的 `coil_id_text`。
