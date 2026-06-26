# Label Studio 圖片破圖修正

原因：舊的 `label_studio_tasks.json` 使用 flatten 後的圖片名稱，且 case_id 被解析成 `raw`，所以 Label Studio 找不到圖片。

## 新流程

現在 tasks JSON 會直接指向原始 Case 資料夾：

```text
data/raw/20220930_095258_KLC9857F/20220930_095258_KLC9857F_cam01.jpeg
```

Label Studio 的圖片 URL 會變成：

```text
/data/local-files/?d=20220930_095258_KLC9857F/20220930_095258_KLC9857F_cam01.jpeg
```

## 操作步驟

### 1. 停掉目前 Label Studio

在 PowerShell 視窗按 `Ctrl + C`。

### 2. 重新產生 tasks JSON

```powershell
cd D:\AIProjects\A1\SteelCoilInspection
.\make_label_tasks.ps1
```

### 3. 用正確 Local Files Root 啟動 Label Studio

```powershell
$env:LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED="true"
$env:LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="D:\AIProjects\A1\SteelCoilInspection\data\raw"
uv run label-studio start --port 8080
```

### 4. 建立新 Project

舊 Project 裡的 Tasks 已經是錯誤路徑，建議建立新 Project：

```text
Steel Coil Inspection v2
```

### 5. 匯入新 JSON

匯入：

```text
D:\AIProjects\A1\SteelCoilInspection\data\label_studio_tasks.json
```

### 6. Labeling Setup

貼上：

```text
D:\AIProjects\A1\SteelCoilInspection\configs\label_studio_config.txt
```

成功後，Task 裡應該看到：

```text
案件：20220930_095258_KLC9857F
車牌：KLC9857F
相機：cam01
```

而不是：

```text
案件：raw
```
