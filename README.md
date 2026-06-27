# Steel Coil Inspection 鋼捲出貨自動稽核系統

本專案使用 `uv` 管理 Python 環境。專案目標不是先做整張圖 OCR，而是先建立「物件標記與偵測」流程，再只針對鋼捲編號區域做 OCR。

## 核心流程

```text
多鏡頭圖片
  ↓
標註資料集
  ↓
YOLO 物件偵測
  ↓
偵測 coil / rubber_pad / chain / tarp / wood_block / trailer
  ↓
裁切鋼捲編號區域
  ↓
OCR 辨識 Coil ID
  ↓
規則引擎產生稽核報告
```

## 第一次初始化

由於 MCP 目前不允許直接寫入 `.toml`，第一次請先執行：

```powershell
cd D:\AIProjects\A1\SteelCoilInspection
.\bootstrap_uv_project.ps1
```

這會建立 `pyproject.toml`，然後執行：

```powershell
uv sync
```

## 整理資料

把原始案件圖片放在：

```text
D:\AIProjects\A1\SteelCoilInspection\data\raw\20220930_095258_KLC9857F\
```

然後執行：

```powershell
.\run_prepare.ps1
```

它會執行：

```powershell
uv run steelcoil init-dirs
uv run steelcoil prepare
uv run steelcoil yolo-yaml
```

## 目前建議標籤

| label | 說明 |
|---|---|
| coil | 鋼捲本體 |
| coil_id_text | 鋼捲上手寫或噴印編號區域 |
| rubber_pad | 黑色膠墊 |
| chain | 鍊條 |
| strap | 鐵帶 / 綁帶 |
| tarp | 藍布、棕布、防水布 |
| wood_block | 木座、木枕 |
| trailer | 拖車 / 車斗 |

## 後續流程

1. 先用 CVAT / Label Studio / LabelImg 標註 `data/labeling/images`
2. 匯出 YOLO 格式資料集到 `data/yolo_dataset`
3. 訓練 YOLO
4. 用模型裁切 `coil_id_text`
5. 對裁切小圖做 OCR
6. 用規則引擎產生稽核報告

## 開發進度 (Development Progress)

### v0.3.0 (2026-06-27)

**專案狀態**
*   **訓練進度**：已完成 50 Epochs 訓練。
*   **模型位置**：`runs\detect\runs\detect\steel_coil-2\weights\best.pt`
*   **模型表現**：
    *   `coil`：預測準確，可用於輔助標註。
    *   `coil_id_text`：準確度低（因訓練數據不足），目前需依賴人工修正。

**已實作功能**
1.  **AI 推論模組** (`src/steelcoil/qt_labeler/inference.py`)
    *   負責載入 `best.pt`。
    *   提供 `predict(image_path)` 方法，回傳預測結果。
2.  **Canvas 視覺化與互動** (`src/steelcoil/qt_labeler/image_canvas.py`)
    *   **視覺區隔**：預測框繪製為「綠色虛線」，人工框為「實線」。
    *   **點擊確認**：預測框中心有小圓圈提示，點擊後轉為正式標註框。
    *   **清空功能**：支援一鍵刪除當前圖片的所有預測框。
3.  **主視窗整合** (`src/steelcoil/qt_labeler/main_window.py`)
    *   **AI 開關**：新增「AI 推論」按鈕，預設關閉。
    *   **停用自動指派**：新標註框預設維持「未指派」。
    *   **強化縮圖選取**：提升視覺對比。

**已知限制**
*   **預測框限制**：目前僅支援「點擊確認」與「刪除」，不支援拖曳微調。
*   **非持久性**：預測框僅為視覺覆蓋層，存檔後不會寫入 annotation 檔案。

---
*更多詳細進度請參考 [dev_progress_v0.3.0.md](dev_progress_v0.3.0.md)*
