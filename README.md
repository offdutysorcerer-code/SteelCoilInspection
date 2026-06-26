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
