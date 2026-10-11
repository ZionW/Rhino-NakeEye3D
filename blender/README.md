# 裸視3D Blender

Blender 5.1.2，外掛0.2.0。開啟 `CyberApple.blend`，外掛已正式安裝啟用，偏好已儲存，重新開啟 Blender 仍可使用。
重新啟動後：Preferences → Add-ons → Install from Disk → 選 `nakedeye3d.zip`，啟用外掛。
3D View 按 N → 裸視3D。開始瞬間保存場景攝影機；暫停凍結；停止恢復攝影機及蘋果部件。

- 空間模式：頭部左右/上下/遠近，右/左手揮動一次旋轉90°。
- 物體模式：單手三指抓握環繞攝影機；雙手只伸食指，部件中心分離1～3倍，攝影機自動退後容納部件。
- Webcam 使用這個專案的 `.venv`、模型及相機授權 helper，UDP39549、預覽39550，與 Rhino 控制通道分開。
- 此版本為本機開發外掛，專案根路徑固定；搬移專案需修改 `ROOT`。先停止 Rhino 追蹤釋放相機。
- 現有三個 apple mesh 為可爆炸部件；一般模型可在物件自訂屬性加入 `nakedeye_part=True`。

`build_demo.py` 可在 Blender Text Editor 執行，建立新的獨立場景；不刪除原有場景。
場景資料來自 `demos/cyberspace.json`，果實12672點、果梗528點、葉片850點，並加入網路节点、線框地面與掃描環。

真人 webcam、頭部攝影機控制、暫停凍結和停止恢復已驗證；預覽用面板的「顯示 Webcam 預覽」開啟本機頁面。
