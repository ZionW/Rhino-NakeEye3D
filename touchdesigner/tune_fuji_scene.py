from pathlib import Path
import json,math
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/fuji_realistic');c=b.op('observer');r=b.op('render')
if not hasattr(b.par,'Parallaxgain'):
    p=b.appendCustomPage('觀看校正').appendFloat('Parallaxgain',label='視差倍率')[0]
    p.min=.2;p.max=2;p.clampMin=True;p.clampMax=True
b.par.Parallaxgain=1
b.op('camera_controller').text=(ROOT/'touchdesigner/fuji_camera_controller.py').read_text()
for name,angles,dim,color in [('sun',(-40,-35),1.05,(1,.94,.86)),('ambient',(-25,135),.85,(.74,.86,1)),('rim',(-55,-155),.65,(.85,.93,1))]:
    light=b.op(name) or b.create(lightCOMP,name)
    light.par.lighttype='distant';light.par.rx=angles[0];light.par.ry=angles[1];light.par.dimmer=dim
    light.par.wcolorr=color[0];light.par.wcolorg=color[1];light.par.wcolorb=color[2]
r.par.lights='sun ambient rim'
for m in b.op('scene').findChildren():
    if m.family!='MAT' or not hasattr(m.par,'diffr'):continue
    rgb=[m.par.diffr.eval(),m.par.diffg.eval(),m.par.diffb.eval()]
    m.par.ambdiff=False
    for name,value in zip(['ambr','ambg','ambb'],rgb):setattr(m.par,name,value*.38)
    if 'asphalt' in m.name.lower():
        m.par.diffr=.16;m.par.diffg=.175;m.par.diffb=.19
        m.par.ambr=.06;m.par.ambg=.07;m.par.ambb=.085
    if 'rock' in m.name.lower():
        m.par.ambr=.13;m.par.ambg=.15;m.par.ambb=.18
    if 'paint' in m.name.lower():
        m.par.shininess=75;m.par.specr=.45;m.par.specg=.45;m.par.specb=.45
active=b.par.Tracking.eval();state=b.fetch('state',{}).copy()
base=state.get('base',b.op('tracker_runtime').module.camera_values())
head=[b.par.Headx.eval(),b.par.Heady.eval(),b.par.Headz.eval()]
b.store('state',{'base':base,'active':True});b.par.Tracking=True
samples=[]
for hx,hz,label in [(0,0,'neutral'),(.15,0,'right'),(0,-.15,'forward')]:
    b.par.Headx=hx;b.par.Heady=0;b.par.Headz=hz;b.op('camera_controller').module.updateCamera()
    b.op('OUT').cook(force=True);b.op('OUT').save(str(ROOT/('touchdesigner/FujiA1-tuned-'+label+'.png')))
    samples.append({'input':[hx,hz],'camera':b.op('tracker_runtime').module.camera_values(),'projection_scale':float(b.op('eye_projection')[0,0])})
assert abs(samples[0]['projection_scale']-samples[2]['projection_scale'])<1e-6
b.par.Headx=0;b.par.Heady=0;b.par.Headz=0;b.op('camera_controller').module.updateCamera()
errors=[(o.path,o.errors(),o.warnings()) for o in b.findChildren() if o.errors() or o.warnings()]
(ROOT/'touchdesigner/FujiA1-tuned-verification.json').write_text(json.dumps({'samples':samples,'errors':errors,'gain':1},indent=2))
b.par.Tracking=False
b.save(str(ROOT/'touchdesigner/FujiA1-realistic.tox'));project.save(str(ROOT/'touchdesigner/FujiA1-realistic.toe'))
b.store('state',state)
b.par.Headx,b.par.Heady,b.par.Headz=head;b.par.Tracking=active
if active:b.op('camera_controller').module.updateCamera()
b.op('OUT').openViewer();b.op('control_panel').openViewer()
print('Scene-relative Rhino parallax and daylight lighting applied; errors',errors)
