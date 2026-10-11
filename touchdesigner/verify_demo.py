import json,math
from pathlib import Path
b=op('/project1/cyber_apple');c=b.op('observer');m=b.op('camera_controller').module
b.par.Demo=False;b.par.Tracking=False;m.onFrameStart(0)
b.par.Tracking=True;m.onFrameStart(1)
initial=[c.par.tx.eval(),c.par.ty.eval(),c.par.tz.eval()]
b.par.Headz=-.2;m.onFrameStart(2)
near=[c.par.tx.eval(),c.par.ty.eval(),c.par.tz.eval()]
assert sum(x*x for x in near)<sum(x*x for x in initial)
b.par.Headz=0;b.par.Viewingmode='object';b.par.Grabbing=True;b.par.Handx=0;b.par.Handy=0;m.onFrameStart(3);b.par.Handx=.2;m.onFrameStart(4)
grip=[c.par.tx.eval(),c.par.ty.eval(),c.par.tz.eval()]
assert sum((a-d)**2 for a,d in zip(initial,grip))>.01
b.par.Grabbing=False;b.par.Exploding=True;b.par.Fingerdistance=.6;m.onFrameStart(5)
for name in ['body','stem','leaf']:b.op(name+'/pointcloud').cook(force=True)
errors=[(n.path,n.errors()) for n in b.findChildren() if n.errors()]
assert not errors,errors
report={'head_depth':True,'grip_orbit':True,'explosion_control':True,'node_errors':errors,'render_size':[b.op('OUT').width,b.op('OUT').height]}
Path('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/verification.json').write_text(json.dumps(report),encoding='utf-8')
b.par.Tracking=False;b.par.Exploding=False;b.par.Grabbing=False;b.par.Handx=0;b.par.Headz=0;b.par.Viewingmode='space';b.par.Demo=True;b.unstore('state');m.onFrameStart(6)
b.save('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/CyberApple.tox')
project.save('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/CyberApple.toe')
print(report)
