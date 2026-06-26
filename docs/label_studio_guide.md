# Label Studio 使用流程

## 1. 啟動 Label Studio

```powershell
cd D:\AIProjects\A1\SteelCoilInspection
.\bootstrap_uv_project.ps1
.\run_prepare.ps1
.\run_label_studio.ps1
```

打開瀏覽器：

```text
http://localhost:8080
```

第一次啟動會要求建立帳號。

## 2. 建立專案

在 Label Studio 裡：

1. New Project
2. Project Name：`Steel Coil Inspection`
3. Import data：選擇 `data/labeling/label_studio_tasks.json`
4. Labeling Setup：選 Custom Template
5. 將 `configs/label_studio_config.txt` 內容貼進去
6. Save

## 3. 標註標籤

使用矩形框標註：

- coil
- coil_id_text
- rubber_pad
- chain
- strap
- tarp
- wood_block
- trailer

## 4. 匯出

標完後在 Label Studio：

1. Project 頁面
2. Export
3. 選 YOLO 或 COCO
4. 下載 zip
5. 解壓到 `data/yolo_dataset`

若 Label Studio 匯出的格式不是 YOLO，後續再加轉換腳本。

## 5. 注意

目前先標少量資料即可，建議先標 14 張範例圖，檢查標籤定義是否合理。
