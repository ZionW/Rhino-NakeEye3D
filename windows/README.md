# 裸視3D — Windows Rhino 8 測試版

適用 Windows 10/11 x64、Rhino 8（.NET 7）、Python 3.11 x64。

1. 解壓縮整個資料夾至可寫入的位置，例如 `C:\Users\你的帳號\Documents\NakedEye3D`；不要直接在 ZIP 內執行。
2. 如尚未安裝 Python，從 https://www.python.org/downloads/windows/ 安裝 Python 3.11 x64，保留 Python Launcher。
3. 雙擊 `windows\Install.cmd`，建立獨立 Python 環境並從 PyPI 安裝 webcam 套件，需要網路。
4. 開啟 Rhino 8，在命令列執行 `_-ScriptEditor _Run`，選取 `windows\OpenPanel.py`。日後輸入 `NakedEye3DPanel` 即可開啟面板。
5. 可先雙擊 `windows\CheckSetup.cmd` 驗證依賴、追蹤模型與動畫；通過後再進入 Rhino。
6. 選取透視視窗，按「開始／繼續追蹤」。開始時記錄目前攝影機作為基準。

## 操作

- 空間模式：頭部左右、上下、前後移動控制視角。
- 物體模式：拇指、食指與中指抓握旋轉攝影機；期間暫停頭部控制。
- 雙手各伸食指：拉開展開爆炸圖；靠攏、放開或按「收回爆炸圖」還原。
- 全螢幕：執行 Rhino 原生 `_Fullscreen` 指令；Esc 退出，還原進入前視角。
- 中／英／日介面、使用說明視窗、視角幅度與靈敏度滑桿。
- 面板附屬 Rhino 主視窗，不設定系統最上層。揮手功能停用。

## 問題排除

Windows 設定 → 隱私權與安全性 → 相機，允許桌面應用程式使用相機。
若 webcam 被占用，先停止其他軟體的追蹤；如果畫面不出現，停止後改相機編號再啟動。
錯誤記錄在 `runtime\webcam.log`；需要復原攝影機時按「停止並還原視角」。
此包已在 macOS 完成語法與打包檢查，尚未在 Windows 硬體執行。請先以模型副本測試。
