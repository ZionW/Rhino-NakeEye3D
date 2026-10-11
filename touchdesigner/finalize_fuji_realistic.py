from pathlib import Path
import math,json
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/fuji_realistic');r=b.op('render');c=b.op('observer')
r.par.bgcolora=1
amb=b.op('ambient');amb.par.lighttype='distant';amb.par.rx=45;amb.par.ry=-140;amb.par.dimmer=.65
b.op('sun').par.lighttype='distant';b.op('sun').par.dimmer=1.1
r.par.lights='sun ambient'
matrix=b.op('eye_projection') or b.create(tableDAT,'eye_projection')
controller=b.op('camera_controller')
controller.text=controller.text.replace('    c.par.rx=rx;c.par.ry=ry', '''    c.par.rx=rx;c.par.ry=ry
    d0=radius*.65;d=max(d0*.3,d0+dz)
    halfw=d0*math.tan(math.radians(c.par.fov.eval()/2));halfh=halfw/(1280/720)
    n=.05;f=5000
    matrix=b.op('eye_projection');matrix.clear()
    for row in [[d/halfw,0,-dx/halfw,0],[0,d/halfh,-dy/halfh,0],[0,0,-f/(f-n),-f*n/(f-n)],[0,0,-1,0]]:matrix.appendRow(row)
    c.par.projection='custommatrix';c.par.projmatrixop=matrix
''')
# Numerical input test follows the same camera update as webcam data.
baseline=b.op('tracker_runtime').module.camera_values()
b.par.Tracking=True;b.store('state',{'base':baseline,'active':True})
samples=[]
for x,z,label in [(0,0,'neutral'),(.2,0,'right'),(0,-.15,'forward')]:
    b.par.Headx=x;b.par.Headz=z
    controller.module.updateCamera()
    b.op('OUT').cook(force=True)
    b.op('OUT').save(str(ROOT/('touchdesigner/FujiA1-test-'+label+'.png')))
    samples.append({'input':[x,z],'camera':b.op('tracker_runtime').module.camera_values(),'matrix':[[float(cell) for cell in row] for row in matrix.rows()]})
b.par.Headx=0;b.par.Headz=0;controller.module.updateCamera();b.par.Tracking=False;b.unstore('state')
b.op('OUT').cook(force=True);b.op('OUT').save(str(ROOT/'touchdesigner/FujiA1-realistic-preview.png'))
errors=[(o.path,o.errors(),o.warnings()) for o in b.findChildren() if o.errors() or o.warnings()]
(ROOT/'touchdesigner/FujiA1-realistic-verification.json').write_text(json.dumps({'samples':samples,'errors':errors},indent=2))
b.save(str(ROOT/'touchdesigner/FujiA1-realistic.tox'));project.save(str(ROOT/'touchdesigner/FujiA1-realistic.toe'))
b.op('OUT').openViewer()
print('Projection tests saved; errors',errors)
