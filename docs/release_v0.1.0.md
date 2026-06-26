# Release v0.1.0 - Steel Coil Labeler MVP

## 版本定位

`v0.1.0` 是 SteelCoilInspection 的第一個可用版本，重點是完成一套不依賴 Label Studio 的 Case First 標註工具。

## 主要成果

- 建立 Qt 桌面版標註工具。
- 支援一個 Case 對應多張 Camera 圖片。
- 支援 YOLO 物件框標註與匯出。
- 支援自動儲存與復原。
- 支援巢狀標註，例如 `coil` 內的 `coil_id_text`。
- 支援 Resize Handles，可直接拖曳調整框大小。
- 已封存 Label Studio 舊方案。

## 使用方式

```powershell
cd D:\AIProjects\A1\SteelCoilInspection
.\run_case_labeler.ps1
```

開啟後選擇 Case 資料夾，例如：

```text
D:\AIProjects\A1\SteelCoilInspection\data\raw\20220930_095258_KLC9857F
```

## 目前 Label

| 快捷鍵 | Label |
|---|---|
| 1 | coil |
| 2 | coil_id_text |
| 3 | rubber_pad |
| 4 | chain |
| 5 | strap |
| 6 | tarp |
| 7 | wood_block |
| 8 | trailer |

## 下一階段

`v0.2.0` 預計加入：

- Track ID：跨 Camera 關聯同一顆鋼捲。
- Case 檢查面板。
- 更完整的資料集匯出與 train / val split。
