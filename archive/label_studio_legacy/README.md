# Label Studio Legacy Archive

本目錄封存第一版 Label Studio 標註流程。

此方案已停止作為主流程，原因：

- Label Studio 1.23.0 的 `/data/local-files/` 在目前環境未成功啟用。
- 外部 HTTP 圖片服務又遇到 CORS / 載入限制。
- 本專案資料是 Case First：一台車次包含 cam01～cam14 多視角，不適合用一般單張圖片標註流程管理。

後續主流程改為：

```text
Case 資料夾
  ↓
Qt 專屬標註工具
  ↓
.steelcoil_annotations.json
  ↓
YOLO Dataset
  ↓
YOLO 訓練 / OCR / Rule Engine
```

## 封存內容

預計封存：

- Label Studio 啟動腳本
- Label Studio 匯入 JSON 產生器
- Label Studio 標註模板
- 舊的圖片 HTTP server 腳本
- Label Studio 操作說明文件
- 舊的 `data/labeling` 中介資料

## 注意

這些檔案只供參考，不再建議直接使用。
