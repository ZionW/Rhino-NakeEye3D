import json,time
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/fuji_realistic')
source=(ROOT/'touchdesigner/build_control_panel.py').read_text()
source=source.replace("op('/project1/cyber_apple')","op('/project1/fuji_realistic')")
source=source.replace(",('Space','空間模式'),('Object','物體模式')",'')
source=source.replace("['三指抓握：旋轉','雙食指：爆炸圖','先停止其他追蹤']","['頭部左右：視差','頭部遠近：深度','以開始位置為基準']")
SKIP_SAVE=True
exec(compile(source,'controls.py','exec'))
live={'time':time.time(),'status':b.par.Status.eval(),'head':[b.par.Headx.eval(),b.par.Heady.eval(),b.par.Headz.eval()],
      'baseline':b.fetch('state',{}).get('base'),'camera':b.op('tracker_runtime').module.camera_values()}
(ROOT/'touchdesigner/FujiA1-realistic-live.json').write_text(json.dumps(live,indent=2))
active=b.par.Tracking.eval();b.par.Tracking=False
b.save(str(ROOT/'touchdesigner/FujiA1-realistic.tox'));project.save(str(ROOT/'touchdesigner/FujiA1-realistic.toe'))
b.par.Tracking=active
b.op('OUT').openViewer();b.op('control_panel').openViewer()
print(live)
