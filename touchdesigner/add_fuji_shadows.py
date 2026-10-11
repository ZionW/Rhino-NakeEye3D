from pathlib import Path
import math
b=op('/project1/fuji_realistic');sun=b.op('sun');a=math.radians(sun.par.ry.eval());p=math.radians(sun.par.rx.eval())
sun.par.tx=math.sin(a)*math.cos(p)*30;sun.par.ty=-math.sin(p)*30;sun.par.tz=math.cos(a)*math.cos(p)*30
sun.par.shadowtype='soft2d';sun.par.orthowidth=45;sun.par.near=.1;sun.par.far=100;sun.par.maxshadowsoftness=.025
sun.par.shadowcasters=b.op('render').par.geometry.eval()
b.op('OUT').cook(force=True);b.op('OUT').save('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/FujiA1-lighting-preview.png')
active=b.par.Tracking.eval();b.par.Tracking=False
b.save('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/FujiA1-realistic.tox');project.save('/Users/zionw/Desktop/Codex/裸視3D/touchdesigner/FujiA1-realistic.toe')
b.par.Tracking=active
print('Soft shadows saved',b.op('render').errors(),b.op('render').warnings())
