# 裸視3D · NakedEye3D

[中文](README.md) · [English](README.en.md)

以 webcam 追蹤頭部與手勢，控制普通螢幕上的 3D 視角。本專案包含 Rhino 外掛、Blender 外掛與 TouchDesigner 示範，提供單人觀看的頭部視差效果；不是雙眼立體顯示。單 webcam 的遠近估算尚未完成實體螢幕尺寸校正。

## Rhino 功能

- **空間模式**：頭部左右、上下、前後移動控制攝影機。
- **物體模式**：拇指、食指與中指抓握後移動手掌，環繞目標旋轉攝影機；抓握期間暫停頭部控制。
- **爆炸圖**：雙手各伸食指，拉開展開、靠攏或解除手勢還原。攝影機自動取景；可用按鈕收回至原位置。至少需要兩個獨立零件。
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

完整說明：[Windows 安裝說明](windows/README.md)。原始碼版本需先編譯 `.rhp`；ZIP 已包含編譯檔、模型與遮罩。

## macOS 與開發

Mac 版已實測 Rhino 攝影機控制、還原、webcam 與模擬手勢；Windows 包已建置並檢查，尚未在 Windows 硬體執行。請先以模型副本測試。

```sh
dotnet build rhino/NakedEye3D.csproj
python3 -m unittest discover -s tools -p 'test_hand_gestures.py'
```

`rhino/TrackingPanel.py` 為 Eto 浮動面板，`ViewportTracking.py` 管理投影與旋轉，`ExplodedView.py` 管理零件位置，`tools/webcam_tracker.py` 為獨立追蹤程序。Windows 的 `OpenPanel.py` 會設定專案路徑與啟動指令。

macOS webcam 程序使用 `tools/NakedEye3D Webcam.app`。自行重建時需準備 Python 依賴及相機用途聲明；現有本機 App 不屬於 Windows 安裝包。

## Blender 與 TouchDesigner

- [Blender 說明](blender/README.md)：`blender/nakedeye3d.zip` 外掛；`CyberApple.blend` 點雲蘋果與 `FujiA1.blend` 場景。
- [TouchDesigner 說明](touchdesigner/README.md)：點雲示範，以及 `FujiA1-realistic.toe` 富士賽車場與 Audi A1 場景。
- [場景說明](FUJI_A1.md)。場景為程序建立的示範，並非官方賽道或車輛 CAD。

三套軟體各自控制攝影機，共用本機 webcam 追蹤程式；同時只有一套可以占用 webcam。Blender / TouchDesigner 的 Windows 移植尚未包含在本次 Rhino 安裝包內。

## 資料與第三方素材

追蹤與預覽服務僅綁定本機 `127.0.0.1`，應用程式不儲存 webcam 影像。臉部 GIF 是視覺遮罩，不是匿名化保證。`runtime/`、Python 環境、快取與本機紀錄不納入版本控制。

追蹤模型來自 Google MediaPipe；GIF 遮罩為使用者提供素材。第三方模型、商標與素材各自權利屬於原權利人。本專案沒有為這些素材另行授予授權。
