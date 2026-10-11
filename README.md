# Rhino NakeEye3D · 裸視3D

[中文](README.md) · [English](README.en.md)

**測試版：功能尚不完善，仍有已知問題，請使用模型副本測試。** 笑面男圖片僅為向《攻殼機動隊》致敬及功能測試使用，之後會更換；其權利屬原權利人。

## Rhino 9 測試畫面

空間模式與 webcam 面板：

![空間模式](docs/images/rhino9-space-mode.png)

物體模式／爆炸圖測試（取景效果仍在調整）：

![爆炸圖測試](docs/images/rhino9-exploded-view.png)

以 webcam 追蹤頭部與手勢，控制普通螢幕上的 3D 視角。本專案僅包含 Rhino 外掛，提供單人觀看的頭部視差效果；不是雙眼立體顯示。單 webcam 的遠近估算尚未完成實體螢幕尺寸校正。

## Rhino 功能

- **空間模式**：頭部左右、上下、前後移動控制攝影機。
- **物體模式**：拇指、食指與中指抓握後移動手掌，環繞目標旋轉攝影機；抓握期間暫停頭部控制。
- **爆炸圖**：可選雙手食指或單手握拳／張掌，調整展開程度與爆炸比例；遺失手部時逐漸還原。攝影機自動取景；可用按鈕收回至原位置。至少需要兩個獨立零件。
- 每次開始／繼續，以目前透視視窗攝影機為基準；停止時還原。
- 中／英／日介面、獨立使用說明視窗、視角幅度與靈敏度滑桿。
- 224×168 webcam 預覽、GIF 臉部遮罩、手部骨架與抓握狀態球。眼睛提示已取消。
- 揮手旋轉已停用。面板附屬 Rhino，沒有系統最上層設定。
- 全螢幕按鈕執行 Rhino `_Fullscreen` 指令，Esc 返回。**目前 Mac Rhino 8 不支援該指令**；Windows 版本待實機確認。

## Windows Rhino 8 安裝

需求：Windows 10/11 x64、Rhino 8、Python 3.11 x64；安裝依賴時需要網路。

1. 下載 [Windows 測試包](dist/NakedEye3D-Windows-Rhino8.zip)，解壓縮至可寫入資料夾。
2. 雙擊 `windows\Install.cmd` 建立獨立 Python 環境並安裝依賴。
3. 可執行 `windows\CheckSetup.cmd` 檢查模型與依賴，不會開啟相機。
4. 在 Rhino 命令列執行 `_-ScriptEditor _Run`，選取 `windows\OpenPanel.py`。
5. 日後輸入 `NakedEye3DPanel` 開啟面板，選擇透視視窗，按「開始／繼續追蹤」。

外掛直接使用目前開啟的 Rhino 檔案；開啟面板不會載入測試檔或加入範例物件。開始追蹤時，以目前作用中的透視視窗與攝影機設定為基準。

正式 Rhino 面板測試版：編譯 `rhino/DockedPanel/RhinoNakeEye3D.Panel.csproj`，使用 Rhino 的 `TestLoadPlugin` 選取產生的 `RhinoNakeEye3D.DockPanel.rhp`，再執行 `rhino/OpenDockedPanel.py`。Windows 使用 Rhino 分頁面板；Mac 使用 Rhino 管理的浮動面板。Rhino 9 macOS 已測試側邊停駐、webcam 預覽與頭部追蹤；Windows 尚待實機驗證。新版 Release 包含 Yak。

完整說明：[Windows 安裝說明](windows/README.md)。原始碼版本需先編譯 `.rhp`；ZIP 已包含編譯檔、模型與遮罩。

## macOS 與開發

Mac 版已實測 Rhino 攝影機控制、還原、webcam 與模擬手勢；Windows 包已建置並檢查，尚未在 Windows 硬體執行。請先以模型副本測試。

```sh
dotnet build rhino/NakedEye3D.csproj
python3 -m unittest discover -s tools -p 'test_hand_gestures.py'
```

`rhino/TrackingPanel.py` 為 Eto 浮動面板，`ViewportTracking.py` 管理投影與旋轉，`ExplodedView.py` 管理零件位置，`tools/webcam_tracker.py` 為獨立追蹤程序。Windows 的 `OpenPanel.py` 會設定專案路徑與啟動指令。

macOS webcam 程序使用 `tools/NakedEye3D Webcam.app`。自行重建時需準備 Python 依賴及相機用途聲明；現有本機 App 不屬於 Windows 安裝包。

## 資料與第三方素材

追蹤與預覽服務僅綁定本機 `127.0.0.1`，預覽會將單張影像暫存於本機 `runtime/preview.jpg` 並持續覆寫，不上傳。臉部 GIF 是視覺遮罩，不是匿名化保證。`runtime/`、Python 環境、快取與本機紀錄不納入版本控制。

追蹤模型來自 Google MediaPipe；GIF 遮罩為使用者提供素材。第三方模型、商標與素材各自權利屬於原權利人。本專案沒有為這些素材另行授予授權。

## Yak 測試套件（Rhino 8.35+ / Rhino 9）

使用 dist 中對應版本的 .yak。Rhino 執行 `PackageManager`，使用「從檔案安裝」，選擇套件後重新啟動 Rhino。首次 Webcam 使用前，以 Python 3.11 執行安裝目錄內 `tools/setup_yak_runtime.py`（需要網路下載套件）。Windows：`py -3.11 tools/setup_yak_runtime.py`；Mac：`python3.11 tools/setup_yak_runtime.py`。執行 `NakeEye3DDockPanel` 開啟面板。此版本尚未發布至 Yak 伺服器；Rhino 9 macOS 已進行面板、鏡頭預覽與頭部追蹤測試；完整手勢與不同硬體穩定性仍待驗證。
