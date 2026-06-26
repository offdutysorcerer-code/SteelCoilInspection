# 稽核規則草案

本文件先定義第一版規則，後續依現場標準調整。

## 基本檢查

### 鋼捲識別

- 每個案件至少應偵測到 1 個 `coil`。
- 若有 `coil`，應盡量偵測到 `coil_id_text`。
- `coil_id_text` 裁切後才交給 OCR。

### 固定狀態

- 鋼捲應有 `steel_strap` 或 `chain` 類固定物。
- 若鋼捲存在但沒有偵測到任何固定物，判定為 `REVIEW`。

### 防滑與支撐

- 鋼捲下方或兩側應有 `rubber_pad` 或 `wood_block`。
- 若有鋼捲但沒有任何墊材，判定為 `REVIEW`。

### 防水布

- `tarp` 是否必要需依作業標準設定。
- 第一版只偵測是否存在，不直接判定異常。

## 報告輸出欄位

| 欄位 | 說明 |
|---|---|
| case_id | 案件資料夾名稱 |
| image | 圖片名稱 |
| coil_count | 鋼捲數量 |
| coil_id_text_count | 編號區域數量 |
| rubber_pad_count | 橡膠墊數量 |
| wood_block_count | 木座數量 |
| strap_count | 綁帶數量 |
| chain_count | 鏈條數量 |
| tarp_count | 防水布數量 |
| status | PASS / REVIEW |
| notes | 判斷原因 |

## 第一版判定邏輯

```text
若 coil_count == 0：REVIEW，原因：未偵測到鋼捲
若 coil_count > 0 且 coil_id_text_count == 0：REVIEW，原因：未偵測到鋼捲編號區域
若 coil_count > 0 且 strap_count + chain_count == 0：REVIEW，原因：未偵測到固定物
若 coil_count > 0 且 rubber_pad_count + wood_block_count == 0：REVIEW，原因：未偵測到墊材或木座
其他：PASS
```

這些只是初版規則，正式使用前需要依現場安全規範修正。
