# Case First 架構

本專案的核心單位不是單張照片，而是「一台車次 / 一個案件」。

## Case 定義

資料夾名稱格式：

```text
YYYYMMDD_HHMMSS_PLATE
```

例如：

```text
20220930_095258_KLC9857F
```

代表：

| 欄位 | 值 |
|---|---|
| 日期 | 2022-09-30 |
| 時間 | 09:52:58 |
| 車牌 | KLC9857F |

## Image 定義

每個 Case 內有多張相機照片：

```text
20220930_095258_KLC9857F_cam01.jpeg
20220930_095258_KLC9857F_cam02.jpeg
...
20220930_095258_KLC9857F_cam14.jpeg
```

每張照片代表同一台車、同一次鋼捲出貨的不同視角。

## AI Pipeline

```text
Case
  ↓
讀取 cam01 ~ cam14
  ↓
每張圖做 YOLO 偵測
  ↓
每張圖裁切 coil_id_text
  ↓
OCR 辨識 Coil ID
  ↓
Case Fusion 整合多視角結果
  ↓
Rule Engine 判斷是否需覆核
  ↓
產生 Case Report
```

## 原則

### 1. 單張照片不直接判定異常

某些攝影機看不到鋼捲、木座、膠墊、鍊條是正常現象。

錯誤做法：

```text
cam08 沒有看到 coil，因此 FAIL
```

正確做法：

```text
Case 中至少有多個角度看到 coil，因此 coil_present = true
```

### 2. YOLO 只負責抽取資訊

YOLO 不判斷是否合格，只輸出：

- 物件類別
- bounding box
- confidence
- camera
- image path

### 3. OCR 只針對 coil_id_text 小區域

不對整張圖 OCR。

### 4. 最終判斷由 Case Fusion + Rule Engine 完成

例如：

- 至少一張圖看到 Coil ID
- 多個 Coil ID 結果是否一致
- 是否有看到 coil
- 是否有看到 chain / strap / rubber_pad / wood_block
- 若信心不足，標為 REVIEW，而不是 FAIL

## 輸出結構

```text
reports/
└─ 20220930_095258_KLC9857F/
   ├─ case_report.json
   ├─ case_report.md
   ├─ detections.json
   └─ ocr_results.json
```
