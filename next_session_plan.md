# SteelCoilInspection - 下階段開發規劃 (v0.3.0)

## 1. 目前專案狀態報告
*   **訓練進度**：已完成 50 Epochs 訓練。
*   **模型位置**：`D:\AIProjects\A1\SteelCoilInspection\runs\detect\runs\detect\steel_coil-2\weights\best.pt`
*   **訓練結果摘要**：
    *   數據量極少（Train: 12, Val: 2），目前僅能作為「流程驗證」。
    *   `coil` mAP50: 0.595 (有基礎偵測能力)。
    *   `coil_id_text` mAP50: 0 (數據不足)。
    *   結論：模型已可載入，可進行下一步的「AI 預標註」整合。

## 2. 下階段目標：v0.3.0 AI 輔助標註 (AI Assist)
**核心任務**：將訓練好的 YOLO 模型整合至 Qt Labeler，實現「開啟圖片時自動顯示預測框」，讓使用者僅需「確認或修正」即可。

### 2.1 實作架構
1.  **新增 `src/steelcoil/qt_labeler/inference.py`**：
    *   負責載入 `best.pt`。
    *   提供 `predict(image_path)` 方法，回傳預測結果 (Boxes, Labels, Confidences)。
2.  **修改 `src/steelcoil/qt_labeler/main_window.py`**：
    *   啟動時載入模型。
    *   當切換圖片 (`on_image_selected`) 時，觸發推論。
    *   將預測結果傳遞給 Canvas。
3.  **修改 `src/steelcoil/qt_labeler/image_canvas.py`**：
    *   新增 `prediction_boxes` 列表。
    *   繪製邏輯：預測框使用「綠色虛線」，人工框使用「實線」，避免視覺混淆。

### 2.2 關鍵路徑資訊 (供下個對話使用)
*   **專案根目錄**：`D:\AIProjects\A1\SteelCoilInspection`
*   **訓練模型 (best.pt)**：`runs\detect\runs\detect\steel_coil-2\weights\best.pt`
*   **需要修改的核心檔案**：
    *   `src/steelcoil/qt_labeler/inference.py` (需建立)
    *   `src/steelcoil/qt_labeler/main_window.py`
    *   `src/steelcoil/qt_labeler/image_canvas.py`

## 3. 下個對話優先執行事項 (Priority Actions)
1.  **確認環境**：確認 `ultralytics` 已安裝且模型路徑正確。
2.  **建立推論模組**：撰寫 `inference.py`，測試能否正確讀取圖片並輸出 BBox。
3.  **Canvas 繪圖整合**：實作預測框的繪製邏輯 (虛線/不同顏色)。
4.  **UI 整合**：在 MainWindow 中加入「開始/停止 AI 推論」按鈕。

---
*文件產生時間：2026-06-27*
*上一階段結束原因：對話上下文限制*
