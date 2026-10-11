"""Run in TouchDesigner Textport; imports the Blender mesh scene and tracking."""
from pathlib import Path
import math
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
parent_op=op('/project1')
b=parent_op.op('fuji_realistic') or parent_op.create(baseCOMP,'fuji_realistic')
page=b.appendCustomPage('裸視3D')
mode=page.appendMenu('Viewingmode',label='觀看模式')[0]
mode.menuNames=['space','object'];mode.menuLabels=['空間模式','物體模式']
for name in ['Tracking','Demo','Grabbing','Exploding']:
    page.appendToggle(name)[0].val=False
for name,val in [('Headx',0),('Heady',0),('Headz',0),('Handx',0),('Handy',0),('Fingerdistance',.08)]:
    page.appendFloat(name)[0].val=val
for name,label in [('Start','開始 / 繼續'),('Pause','暫停'),('Stop','停止並恢復'),('Calibrate','以目前視角校正')]:page.appendPulse(name,label=label)
page.appendInt('Camera',label='Webcam 編號')[0].val=0
page.appendStr('Status',label='追蹤狀態')[0].val='已停止'
scene=b.create(fbxCOMP,'scene')
scene.par.file=str(ROOT/'touchdesigner/FujiA1-realistic.fbx');scene.par.imp.pulse()
scene.par.sx=.01;scene.par.sy=.01;scene.par.sz=.01
cam=b.create(cameraCOMP,'observer')
cam.par.tx=5.6;cam.par.ty=2.1;cam.par.tz=8
cam.par.ry=math.degrees(math.atan2(5.6,9));cam.par.rx=-math.degrees(math.atan2(.9,math.hypot(5.6,9)))
cam.par.fov=54.4;cam.par.far=5000
sun=b.create(lightCOMP,'sun');sun.par.tx=8;sun.par.ty=20;sun.par.tz=12
sun.par.rx=-50;sun.par.ry=30
render=b.create(renderTOP,'render');render.par.camera=cam
geos=scene.findChildren(type=geometryCOMP)
render.par.geometry=' '.join(o.path for o in geos);render.par.lights=sun.path
render.par.resolutionw=1280;render.par.resolutionh=720
render.par.bgcolorr=.36;render.par.bgcolorg=.52;render.par.bgcolorb=.68;render.par.bgcolora=1
out=b.create(nullTOP,'OUT');out.inputConnectors[0].connect(render)
runtime=b.create(textDAT,'tracker_runtime');runtime.text=(ROOT/'touchdesigner/tracker_runtime.py').read_text()
buttons=b.create(parameterexecuteDAT,'tracking_buttons');buttons.par.op=b;buttons.par.pars='Start Pause Stop Calibrate';buttons.par.onpulse=True
buttons.text="def onPulse(par):\n    m=parent().op('tracker_runtime').module\n    {'Start':m.start,'Pause':m.pause,'Stop':m.stop,'Calibrate':m.calibrate}[par.name]()\n"
preview=b.create(scriptTOP,'tracking_preview');cb=b.create(textDAT,'preview_callbacks')
cb.text="""import numpy as np,urllib.request
_last=np.zeros((168,224,4),dtype=np.uint8)
_last[:,:,3]=255
def onCook(scriptOp):
    global _last
    try:
        with urllib.request.urlopen('http://127.0.0.1:39560/rgba',timeout=.1) as r:data=r.read()
        if len(data)==168*224*4:_last=np.frombuffer(data,dtype=np.uint8).reshape((168,224,4)).copy()
    except Exception:pass
    scriptOp.copyNumpyArray(np.flipud(_last).copy())
"""
preview.par.callbacks=cb
controller=b.create(executeDAT,'camera_controller');controller.par.framestart=True;controller.par.exit=True
controller.text="""import math
def updateCamera():
    b=parent();c=b.op('observer');s=b.fetch('state',{})
    if not b.par.Tracking or not s.get('base'):return
    x,y,z,rx,ry=s['base'];a=math.radians(ry);p=math.radians(rx)
    radius=math.sqrt(x*x+y*y+z*z)
    dx=b.par.Headx.eval()*radius*.45;dy=b.par.Heady.eval()*radius*.45;dz=b.par.Headz.eval()*radius
    c.par.tx=x+dx*math.cos(a)+dz*math.sin(a)*math.cos(p)
    c.par.ty=y+dy-dz*math.sin(p)
    c.par.tz=z-dx*math.sin(a)+dz*math.cos(a)*math.cos(p)
    c.par.rx=rx;c.par.ry=ry
def onFrameStart(frame):
    if parent().op('tracker_runtime').module.tick():updateCamera()
def onExit():parent().op('tracker_runtime').module.stop()
"""
b.op('OUT').cook(force=True)
out.save(str(ROOT/'touchdesigner/FujiA1-realistic-preview.png'))
b.save(str(ROOT/'touchdesigner/FujiA1-realistic.tox'))
project.save(str(ROOT/'touchdesigner/FujiA1-realistic.toe'))
print('Imported mesh scene',len(geos),'geometry COMPs; output',out.width,out.height)
