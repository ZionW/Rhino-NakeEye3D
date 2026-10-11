from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/cyber_apple')
old=b.op('tracker_runtime')
if old:
    try:old.module.stop()
    except Exception:pass
page=b.appendCustomPage('追蹤控制')
for name,label in [('Start','開始 / 繼續'),('Pause','暫停'),('Stop','停止並恢復'),('Calibrate','以目前視角校正')]:
    if not hasattr(b.par,name):page.appendPulse(name,label=label)
if not hasattr(b.par,'Camera'):
    p=page.appendInt('Camera',label='Webcam 編號')[0];p.val=0;p.min=0;p.max=8
if not hasattr(b.par,'Status'):
    p=page.appendStr('Status',label='狀態')[0];p.val='已停止';p.readOnly=True
runtime=b.op('tracker_runtime') or b.create(textDAT,'tracker_runtime');runtime.text=(ROOT/'touchdesigner/tracker_runtime.py').read_text(encoding='utf-8')
pulses=b.op('tracking_buttons') or b.create(parameterexecuteDAT,'tracking_buttons')
pulses.par.op=b;pulses.par.pars='Start Pause Stop Calibrate';pulses.par.onpulse=True
pulses.text='''def onPulse(par):
    m=parent().op('tracker_runtime').module
    {'Start':m.start,'Pause':m.pause,'Stop':m.stop,'Calibrate':m.calibrate}[par.name]()
'''
controller=b.op('camera_controller')
text=controller.text
if 'def updateCamera' not in text:
    text=text.replace('def onFrameStart(frame):','def updateCamera(frame):')
    text+='''\ndef onFrameStart(frame):
    m=parent().op('tracker_runtime').module
    if m.tick() or not parent().par.Tracking:updateCamera(frame)
def onExit():
    parent().op('tracker_runtime').module.stop()
'''
    controller.text=text
    controller.par.exit=True
# Native Script TOP receives RGBA bytes in memory; no JPEG decoder dependency.
if b.op('tracking_preview'):b.op('tracking_preview').destroy()
preview=b.create(scriptTOP,'tracking_preview')
cb=b.op('preview_callbacks') or b.create(textDAT,'preview_callbacks')
cb.text="""import numpy as np,urllib.request
_last=np.zeros((168,224,4),dtype=np.uint8)
_last[:,:,3]=255
def onCook(scriptOp):
    global _last
    try:
        with urllib.request.urlopen('http://127.0.0.1:39560/rgba',timeout=.10) as r:data=r.read()
        if len(data)==168*224*4:_last=np.frombuffer(data,dtype=np.uint8).reshape((168,224,4)).copy()
    except Exception:pass
    scriptOp.copyNumpyArray(np.flipud(_last).copy())
"""
preview.par.callbacks=cb
b.par.Demo=False;b.par.Tracking=False
b.save(str(ROOT/'touchdesigner/CyberApple.tox'))
if not globals().get('SKIP_SAVE',False):project.save(str(ROOT/'touchdesigner/CyberApple.toe'))
print('TouchDesigner tracking panel installed',[(p.name,p.eval()) for p in b.customPars if p.name in ['Status','Start','Pause','Stop','Camera']])
