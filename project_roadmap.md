# SteelCoilInspection 專案規劃與交接文件

> 版本基準：v0.1.0  
> 文件目的：作為新聊天室、新開發階段、版本控制與後續功能開發的交接基準。  
> 專案定位：鋼捲進廠／出貨影像辨識、標註、YOLO 訓練、OCR、ERP 比對與檢測報告平台。

---

## 1. 專案背景

本專案原本從「AI 辨識鋼捲標籤及粉筆字」需求開始，最初曾討論是否直接使用 Vision LLM 或 OCR 來辨識鋼捲照片中的資料。

經過實際照片分析後，確認這不是一般文件 OCR 問題，而是一個多攝影機、多視角、以車次為單位的工業影像檢測問題。

因此目前專案方向已調整為：

```text
Case
  ↓
多 Camera 影像
  ↓
專屬 Qt 標註工具
  ↓
YOLO Dataset
  ↓
YOLO Detector
  ↓
coil_id_text OCR
  ↓
ERP / 出貨資料比對
  ↓
Inspection Report
```

專案不是單純的 YOLO 訓練專案，也不是單純 OCR 專案，而是 **Steel Coil Inspection Platform**。

---

## 2. 核心設計理念

### 2.1 Case First

所有資料以 **Case（車次）** 為核心。

一個資料夾代表一台車次：

```text
20220930_095258_KLC9857F
```

資料夾名稱代表：

```text
日期_時間_車牌號碼
```

例如：

```text
20220930_095258_KLC9857F
```

代表：

```text
日期：2022-09-30
時間：09:52:58
車牌：KLC9857F
```

每個 Case 內包含多張照片，每張照片來自不同攝影機，例如：

```text
20220930_095258_KLC9857F_cam01.jpeg
20220930_095258_KLC9857F_cam02.jpeg
...
20220930_095258_KLC9857F_cam14.jpeg
```

### 2.2 Coil First

系統真正的主角不是圖片，也不是 bounding box，而是 **鋼捲（Coil）**。

同一顆鋼捲可能出現在多個 camera 中，也可能某些 camera 看不到。

因此未來資料模型應該從：

```text
Image
  ↓
Boxes
```

升級成：

```text
Case
  ↓
Coils
  ↓
Views
  ↓
Boxes
```

### 2.3 AI 是輔助，不是目的

YOLO、OCR、LLM 都只是工具。專案目的不是炫技，而是讓現場可以更快、更穩定地完成鋼捲辨識與資料核對。

---

## 3. 目前專案狀態

### 3.1 GitHub Repository

```text
https://github.com/offdutysorcerer-code/SteelCoilInspection
```

### 3.2 目前版本

```text
v0.1.0 - Steel Coil Labeler MVP
```

### 3.3 Git 狀態

目前已完成：

```text
git init
git commit
git tag v0.1.0
git push origin main
git push origin v0.1.0
```

### 3.4 專案管理方式

建議後續使用簡化 Git Flow：

```text
main                    穩定版本
feature/track-id        Track ID 開發
feature/case-panel      Case Summary / Case Panel 開發
feature/yolo-assist     YOLO 預標註開發
feature/ocr             OCR 開發
feature/report          報表與 ERP 比對開發
```

每完成一個穩定功能後合併回 `main`，並建立版本 tag。

---

## 4. 已放棄方案：Label Studio

### 4.1 曾嘗試 Label Studio

曾嘗試使用 Label Studio 作為標註工具，但最終放棄。

原因：

1. Label Studio 的 Local File Serving 在目前版本與 Windows 環境下不穩定。
2. `/data/local-files/` 路由無法正常使用。
3. 即使改用 HTTP Server，又遇到 CORS / URL 安全限制。
4. Label Studio 是以單張圖片 Task 為中心，不適合本專案的多 Camera Case 結構。
5. 本專案需要 Case、Camera、Coil Track ID 等客製化資訊，Label Studio 客製成本過高。

本次測試環境中 Label Studio 版本為 `1.23.0`，且 server log 顯示 `/data/local-files/` 請求回傳 404。相關紀錄來自先前上傳的 Label Studio 執行日誌。

### 4.2 Label Studio 相關檔案已封存

目前 Label Studio 舊方案已封存到：

```text
archive/label_studio_legacy/
```

封存目的：

```text
保留歷史紀錄
避免干擾目前主線
未來若需要查詢 Label Studio 嘗試過程，可回來參考
```

後續主線不再使用 Label Studio。

---

## 5. 目前主線：Qt 專屬標註工具

### 5.1 主入口

```powershell
cd D:\AIProjects\A1\SteelCoilInspection
.\run_case_labeler.ps1
```

### 5.2 目前已完成功能

Qt Labeler v0.1.0 已完成：

```text
Case 模式
Camera 縮圖列表
點選縮圖切換圖片
Bounding Box 標註
Label 選擇
Auto Save
YOLO 匯出
滑鼠滾輪縮放
Alt + 左鍵 / 中鍵平移
左鍵拖曳畫框
左鍵點選既有框
右鍵刪框
Delete / Backspace 刪除選取框
Ctrl+Z Undo
Ctrl+C / Ctrl+V 複製貼上框
Resize Handles 四角拖拉調整大小
Box 清單
點 Box 清單可選取框
Case 完成度統計
Label 數量統計
每張圖顯示是否已標
下一張未標
coil 裡面可以標 coil_id_text
```

### 5.3 已修正問題

#### 5.3.1 UI 卡住

第三版曾發生開啟 Case 後 UI 卡死。

原因：

```text
開啟 Case
  ↓
選第一張圖
  ↓
刷新縮圖列表
  ↓
觸發選圖事件
  ↓
重複刷新
  ↓
UI 卡住
```

修正方式：

```text
refresh_thumbnail_list 時 blockSignals
on_image_selected 不再呼叫整體 refresh_all_panels
加入 is_refreshing_ui 防止 re-entry
```

#### 5.3.2 coil 內無法標 coil_id_text

曾發生 `coil_id_text` 被包含在 `coil` 裡時，無法重新框選。

修正後行為：

```text
左鍵點一下框內：選取既有框
左鍵拖曳：不管是否從既有框內開始，都建立新框
```

現在可正常在 `coil` 內標 `coil_id_text`。

---

## 6. 目前 Label 設計

目前使用的 label：

```text
coil
coil_id_text
rubber_pad
wood
chain
strap
truck
trailer
```

### 6.1 label 說明

#### coil

鋼捲主體。

第一階段最重要 label。

#### coil_id_text

鋼捲上可讀取的粉筆字或標籤文字區域。

未來 OCR 僅需對此區域進行辨識。

#### rubber_pad

鋼捲下方或旁邊的橡膠墊。

#### wood

木座、木塊或固定鋼捲用木材。

#### chain

固定鋼捲或車斗的鍊條。

#### strap

鐵帶、綁帶或其他固定帶。

#### truck

車頭或整車。

#### trailer

拖板車、車斗。

---

## 7. 標註規則初稿

### 7.1 coil

標註鋼捲可見外輪廓。

原則：

```text
框住可見主體
遮擋部分不強行猜測完整輪廓
多顆鋼捲分開標
```

### 7.2 coil_id_text

只框文字區域，不框整個鋼捲。

例如：

```text
5079651
5076817
```

注意：

```text
coil_id_text 通常位於 coil 內
允許 nested annotation
coil_id_text 可以被 coil box 包含
```

### 7.3 rubber_pad / wood / chain / strap

第一階段可先不強求完整標註。

建議訓練順序：

```text
第一批：coil + coil_id_text
第二批：wood + rubber_pad
第三批：chain + strap
```

---

## 8. 目前資料與輸出

### 8.1 原始資料

```text
data/raw/
  20220930_095258_KLC9857F/
    20220930_095258_KLC9857F_cam01.jpeg
    ...
    20220930_095258_KLC9857F_cam14.jpeg
```

### 8.2 標註檔案

Qt Labeler 會自動在 Case 資料夾中產生：

```text
.steelcoil_annotations.json
```

此檔案目前儲存每張圖片的 bounding boxes。

### 8.3 YOLO 匯出

目前已可匯出 YOLO 格式資料集。

後續需要增強：

```text
train / val split
dataset.yaml 自動生成
class mapping 固定化
只匯出已標註圖片
匯出前檢查空標註
```

---

## 9. 目前專案架構

概念上目前主結構：

```text
SteelCoilInspection/
├── archive/
│   └── label_studio_legacy/
├── configs/
│   └── labels.yaml
├── data/
│   ├── raw/
│   ├── labeling/
│   └── yolo_dataset/
├── docs/
│   ├── annotation_guide.md
│   ├── case_first_architecture.md
│   ├── inspection_rules.md
│   ├── release_v0.1.0.md
│   └── project_roadmap.md
├── scripts/
│   ├── prepare_dataset.py
│   ├── train_yolo.py
│   ├── infer_yolo.py
│   ├── create_yolo_yaml.py
│   └── crop_coil_id_regions.py
├── src/
│   └── steelcoil/
│       ├── case_importer.py
│       ├── case_model.py
│       ├── cli.py
│       ├── fusion.py
│       ├── paths.py
│       ├── reporting.py
│       ├── yolo_config.py
│       └── qt_labeler/
│           ├── app.py
│           ├── main_window.py
│           ├── image_canvas.py
│           ├── models.py
│           └── yolo_export.py
├── run_case_labeler.ps1
├── run_prepare.ps1
├── bootstrap_uv_project.ps1
├── pyproject.toml
├── uv.lock
├── CHANGELOG.md
└── README.md
```

---

## 10. v0.2.0 規劃：Case Data Model + Track ID

### 10.1 為什麼要重構資料模型

目前 v0.1.0 的資料模型仍偏向：

```text
Image
  ↓
Boxes
```

但本專案的真正關係應該是：

```text
Case
  ↓
Coils
  ↓
Views
  ↓
Boxes
```

這對未來 OCR、ERP 比對與報告都很重要。

### 10.2 目標資料模型

預計 v0.2.0 建立：

```text
CaseAnnotation
├── case_id
├── date
├── time
├── plate
├── images[]
├── coils[]
└── image_annotations[]
```

更細：

```text
Case
  ├── case_id
  ├── date
  ├── time
  ├── plate
  ├── cameras
  │   ├── cam01
  │   ├── cam02
  │   └── ...
  └── coils
      ├── Coil #1
      │   ├── views
      │   │   ├── cam01
      │   │   │   ├── coil bbox
      │   │   │   └── coil_id_text bbox
      │   │   └── cam08
      │   │       └── coil bbox
      │   └── ocr_result
      └── Coil #2
          └── ...
```

### 10.3 Track ID

每個 `coil` 都應該有 Track ID：

```text
Coil #1
Coil #2
Coil #3
```

目的：

```text
跨 Camera 關聯同一顆鋼捲
OCR 結果可歸屬到正確 Coil
報表可依 Coil 輸出
ERP 比對可依 Coil 編號處理
```

### 10.4 Track ID 使用流程

使用者畫一個 `coil`：

```text
如果目前沒有 Coil，系統建立 Coil #1
如果已有 Coil，使用者可指定這個框屬於 Coil #1 / Coil #2 / 新 Coil
```

切換到其他 camera：

```text
看到同一顆鋼捲
  ↓
畫 coil box
  ↓
指定 Track ID = Coil #1
```

---

## 11. v0.2.0 UI 規劃

### 11.1 左側面板改版

目前左側主要是 Camera 縮圖與 box 清單。

v0.2.0 預計改成：

```text
Case
20220930_095258_KLC9857F

Coils
├── Coil #1
│   ├── cam01
│   ├── cam03
│   └── cam08
├── Coil #2
│   ├── cam02
│   └── cam06

Images
├── ✓ cam01
├── ✓ cam02
├── ○ cam03
...
└── ○ cam14
```

### 11.2 Coil Tree

Coil Tree 功能：

```text
顯示每顆 Coil 出現在哪些 camera
點 Coil #1 可高亮所有相關 box
點 cam01 可切換到該 camera
顯示 coil_id_text 是否存在
顯示 OCR 狀態
```

### 11.3 Box 屬性面板

選取 box 後顯示：

```text
Label: coil
Track ID: Coil #1
Camera: cam05
BBox: x, y, w, h
```

如果選取的是 `coil_id_text`：

```text
Label: coil_id_text
Belongs to: Coil #1
OCR Text: 未辨識 / 5079651
```

---

## 12. v0.2.0 開發步驟

### Step 1：建立新的資料模型

新增或重構：

```text
src/steelcoil/qt_labeler/models.py
src/steelcoil/case_model.py
```

目標：

```text
支援 legacy .steelcoil_annotations.json
支援新 schema
開啟舊標註時自動 migration
```

### Step 2：Annotation JSON schema v2

建議新格式：

```json
{
  "schema_version": 2,
  "case": {
    "case_id": "20220930_095258_KLC9857F",
    "date": "2022-09-30",
    "time": "09:52:58",
    "plate": "KLC9857F"
  },
  "coils": [
    {
      "track_id": "coil_001",
      "display_name": "Coil #1",
      "notes": ""
    }
  ],
  "images": [
    {
      "camera": "cam01",
      "filename": "20220930_095258_KLC9857F_cam01.jpeg",
      "boxes": [
        {
          "id": "box_001",
          "label": "coil",
          "track_id": "coil_001",
          "x": 100,
          "y": 200,
          "w": 500,
          "h": 400
        },
        {
          "id": "box_002",
          "label": "coil_id_text",
          "parent_track_id": "coil_001",
          "x": 180,
          "y": 260,
          "w": 120,
          "h": 60
        }
      ]
    }
  ]
}
```

### Step 3：UI 支援 Track ID

功能：

```text
新增 Coil #
指定選取 coil box 的 Track ID
coil_id_text 可指定 parent coil
左側顯示 Coil Tree
```

### Step 4：YOLO 匯出仍保持相容

YOLO 不需要 Track ID。

YOLO 匯出只使用：

```text
label
bbox
image
```

Track ID 留在 `.steelcoil_annotations.json`，供 OCR / ERP / 報表使用。

---

## 13. v0.3.0 規劃：YOLO Training + AI Assist

### 13.1 訓練目標

先訓練：

```text
coil
coil_id_text
```

理由：

```text
這兩個最重要
最容易先看到成果
可立即銜接 OCR
```

第二階段再加入：

```text
rubber_pad
wood
chain
strap
```

### 13.2 YOLO Assist

流程：

```text
人工標註一批資料
  ↓
訓練 YOLO
  ↓
Qt Labeler 內執行推論
  ↓
顯示預測框
  ↓
人工 Accept / Reject / Modify
```

### 13.3 預標註 UI

預計：

```text
AI Predictions
├── coil 0.95
├── coil_id_text 0.88
└── rubber_pad 0.72
```

快捷鍵：

```text
Enter 接受目前預測
A 接受全部高信心預測
R 拒絕目前預測
```

---

## 14. v0.4.0 規劃：OCR

### 14.1 OCR 原則

不做整張圖 OCR。

只對：

```text
coil_id_text bbox
```

進行 OCR。

原因：

```text
減少資源
提升準確率
避免背景干擾
```

### 14.2 OCR 可能技術

候選：

```text
PaddleOCR
Tesseract
EasyOCR
Vision LLM 二次確認
```

優先考慮：

```text
PaddleOCR
```

因為中文、數字、工業標記通常比 Tesseract 穩定。

### 14.3 OCR 結果儲存

預計儲存在 Coil 層級：

```json
{
  "track_id": "coil_001",
  "ocr_candidates": [
    {
      "camera": "cam05",
      "text": "5079651",
      "confidence": 0.93
    },
    {
      "camera": "cam08",
      "text": "5079651",
      "confidence": 0.88
    }
  ],
  "final_ocr": "5079651"
}
```

---

## 15. v0.5.0 規劃：ERP 比對

### 15.1 目標

將 OCR 結果與 ERP / 出貨資料 / 車次資料比對。

例如：

```text
車牌 KLC9857F
預期鋼捲：5079651, 5076817
OCR 辨識：5079651, 5076817
結果：PASS
```

或：

```text
預期鋼捲：5079651, 5076817
OCR 辨識：5079651, 5076818
結果：NG
差異：5076817 vs 5076818
```

### 15.2 比對輸出

預計輸出：

```text
Case Report
Excel
CSV
PDF
```

---

## 16. Report 規劃

### 16.1 Case Report

每個 Case 一份報告：

```text
Case ID
日期
時間
車牌
圖片數量
Coil 數量
每顆 Coil 的 OCR 結果
各 camera 是否有看到 coil
異常項目
```

### 16.2 異常類型

預計：

```text
OCR missing
OCR mismatch
Expected coil missing
Unexpected coil detected
Camera missing
Image missing
Required object missing
```

---

## 17. 目前要避免的事情

### 17.1 不要回到 Label Studio

Label Studio 已證明不適合目前資料結構。

### 17.2 不要直接整張圖 OCR

整張圖 OCR 效率低且不穩。

### 17.3 不要讓 YOLO 判斷最終異常

YOLO 只負責 detection。

最終判斷應該由：

```text
Rule Engine
Case Fusion
ERP Compare
```

完成。

### 17.4 不要把大型圖片與模型放進 Git

Git 應排除：

```text
.venv/
data/raw/
data/labeling/
data/yolo_dataset/images/
data/yolo_dataset/labels/
runs/
models/
outputs/
reports/
```

---

## 18. Git 與版本規劃

### 18.1 版本路線

```text
v0.1.0
Qt Labeler MVP
已完成

v0.2.0
Case Data Model + Track ID
下一步

v0.3.0
YOLO Training + AI Assist

v0.4.0
OCR

v0.5.0
ERP Compare + Reports

v1.0.0
Steel Coil Inspection Platform
```

### 18.2 建議 commit message

```text
Add Track ID data model
Add Coil Tree panel
Add annotation schema migration
Add YOLO export split
Fix nested annotation selection
Fix thumbnail refresh recursion
```

### 18.3 建議 branch

```powershell
git checkout -b feature/track-id
```

完成後：

```powershell
git add .
git commit -m "Add Track ID support"
git push -u origin feature/track-id
```

---

## 19. 下一個聊天室接手指令

如果在新聊天室繼續開發，建議第一句貼：

```text
請閱讀 docs/project_roadmap.md，繼續 SteelCoilInspection 專案開發。目前版本 v0.1.0 已完成 Qt Labeler MVP，下一步請開始 v0.2.0：Case Data Model + Track ID。
```

若需要讓模型先看目前程式：

```text
請先檢查 src/steelcoil/qt_labeler/models.py、main_window.py、image_canvas.py、yolo_export.py，然後提出 v0.2.0 的實作步驟。
```

---

## 20. v0.2.0 立即 TODO

### TODO 1：建立 feature branch

```powershell
git checkout -b feature/track-id
```

### TODO 2：檢查目前 annotation schema

閱讀：

```text
src/steelcoil/qt_labeler/models.py
```

確認目前 `.steelcoil_annotations.json` 格式。

### TODO 3：設計 schema migration

支援：

```text
schema_version 1 → schema_version 2
```

### TODO 4：新增 Track ID 欄位

Box 結構新增：

```text
id
label
track_id
parent_track_id
```

### TODO 5：UI 新增 Coil Tree

左側顯示：

```text
Coils
├── Coil #1
│   ├── cam01
│   └── cam05
└── Coil #2
    └── cam02
```

### TODO 6：YOLO 匯出保持相容

確認 YOLO export 不受 Track ID 影響。

---

## 21. 長期願景

最終工具應該能達成：

```text
匯入 Case
  ↓
AI 預標註
  ↓
人工快速修正
  ↓
YOLO / OCR 自動處理
  ↓
ERP 自動比對
  ↓
產生報告
```

現場使用者理想流程：

```text
選取車次資料夾
  ↓
系統自動辨識鋼捲與編號
  ↓
人工確認異常
  ↓
輸出檢查結果
```

---

## 22. 總結

目前專案已完成第一個穩定可用版本：

```text
v0.1.0 - Steel Coil Labeler MVP
```

下一步不是再加零散功能，而是建立長期可擴充的核心資料模型：

```text
Case → Coil → View → Box
```

這會讓後續 Track ID、YOLO Assist、OCR、ERP 比對、報表都能建立在穩定架構上。

本文件應作為後續開發的主要依據。
