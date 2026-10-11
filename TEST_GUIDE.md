# Rhino 裸視3D 測試 / Rhino testing guide

先以模型副本與透視視窗測試。Windows 安裝見 `windows/README.md`；英文見 `windows/README.en.md`。
Use a copy of your model and activate a perspective viewport first.

1. 輸入 `NakedEye3DPanel`，開始追蹤。開始時記錄目前攝影機。
   Open `NakedEye3DPanel` and start tracking to capture the current camera baseline.
2. 空間模式：左右、上下、前後移動頭部；靠近物件變大，退後變小。
   Space mode: move your head sideways, vertically and forward/backward.
3. 物體模式：拇指、食指、中指抓握，綠球出現後移動手掌旋轉攝影機。
   Object mode: grasp with thumb/index/middle; move your hand after the indicator turns green.
4. 張開手指解除抓握，確認頭部控制恢復。
   Release the grasp and verify head control resumes.
5. 至少兩個獨立物件：双手各伸食指，拉開展開、靠攏或解除還原。
   With at least two separate objects, extend both index fingers to spread parts; bring together or release to restore.
6. 測試「收回爆炸圖」、幅度／靈敏度滑桿、中英日切換及說明視窗。
   Check Restore parts, both sliders, language selection and the Help dialog.
7. Windows：按全螢幕，Esc 返回。Mac Rhino 8 沒有 Fullscreen 指令。
   Windows: test Fullscreen and Esc. Mac Rhino 8 does not support the Fullscreen command.
8. 暫停保持視角；停止還原啟動前視角並釋放 webcam。
   Pause preserves the view; Stop restores the initial view and releases the webcam.

Windows 相機權限需允許桌面程式。若被占用，先關閉其他相機程式。
Allow camera access for desktop applications and close other camera clients.

Windows 版本尚待實機測試；自動回歸涵蓋手勢辨識、零件還原與模擬攝影機控制。
Windows hardware verification is pending; regression checks cover gesture classification, part restoration and simulated camera control.
