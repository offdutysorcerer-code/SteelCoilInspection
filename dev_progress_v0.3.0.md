# SteelCoilInspection v0.3.0 AI 輔助標註開發進度報告

## 📌 專案狀態
*   **訓練進度**：已完成 50 Epochs 訓練。
*   **模型位置**：`D:\AIProjects\A1\SteelCoilInspection\runs\detect\runs\detect\steel_coil-2\weights\best.pt`
*   **模型表現**：
    *   `coil`：預測準確，可用於輔助標註。
    *   `coil_id_text`：準確度低（因訓練數據不足），目前需依賴人工修正。

## 🔧 已實作功能 (v0.3.0)
1.  **AI 推論模組** (`src/steelcoil/qt_labeler/inference.py`)
    *   負責載入 `best.pt`。
    *   提供 `predict(image_path)` 方法，回傳預測結果 (Boxes, Labels, Confidences)。
2.  **Canvas 視覺化與互動** (`src/steelcoil/qt_labeler/image_canvas.py`)
    *   **視覺區隔**：預測框繪製為「綠色虛線」，人工框為「實線」。
    *   **點擊確認**：預測框中心有小圓圈提示，點擊後轉為正式標註框（綠色實線）。
    *   **清空功能**：新增 `clear_predictions()` 方法，支援一鍵刪除當前圖片的所有預測框。
3.  **主視窗整合** (`src/steelcoil/qt_labeler/main_window.py`)
    *   **AI 開關**：新增「AI 推論」按鈕，預設關閉，開啟後切換圖片自動推論。
    *   **停用自動指派**：在 `on_annotation_changed` 中註解掉 `assign_default_track_for_selected_box`，新標註框預設維持「未指派」。
    *   **強化縮圖選取**：使用 QSS (`QListWidget::item:selected`) 設定選取項目為「亮藍色背景 + 白字」，提升視覺對比。

## ⚠️ 已知限制
*   **預測框限制**：目前僅支援「點擊確認」與「刪除」，不支援拖曳微調。
*   **非持久性**：預測框僅為視覺覆蓋層 (Overlay)，存檔後不會寫入 annotation 檔案，下次開啟會重新推論。

## 📂 關鍵路徑資訊
*   **專案根目錄**：`D:\AIProjects\A1\SteelCoilInspection`
*   **啟動腳本**：`D:\AIProjects\A1\SteelCoilInspection\run_case_labeler.ps1`
*   **訓練模型**：`runs\detect\runs\detect\steel_coil-2\weights\best.pt`

## 🔜 建議下階段優先事項
1.  **測試驗證**：確認 v0.3.0 功能 (AI 開關、點擊確認、清空、縮圖選取) 運作正常。
2.  **模型優化**：針對 `coil_id_text` 收集更多訓練圖片並重新訓練。
3.  **效能評估**：評估是否需要實作「預測框拖曳微調」功能。
4.  **版本規劃**：準備 v0.4.0 規劃 (如：批量標註、OCR 輔助、模型自動更新機制)。

---
*報告產生時間：2026-06-27*
*狀態：本地 Git 已提交最新修改，尚未推送到遠端 (origin)*
