"""Run in the existing tracking project; creates a separate Fuji scene file."""
import json,math
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
d=json.loads((ROOT/'demos/fuji_a1.json').read_text(encoding='utf-8'))
b=op('/project1/cyber_apple')
b.op('tracker_runtime').module.stop()
b.par.Demo=False;b.par.Tracking=False;b.par.Viewingmode='space'
centers={key:[sum(p[k] for p in points)/len(points) for k in range(3)] for key,points in d['parts'].items()}
center=[sum(v[k] for v in centers.values())/len(centers) for k in range(3)]
template='''POINTS=%r
COLORS=%r
SIZE=%r
OFFSET=%r
PART=%r
def onCook(scriptOp):
    scriptOp.clear();scriptOp.pointAttribs.create('Cd')
    b=scriptOp.parent(2)
    f=1+2*max(0,min(1,(b.par.Fingerdistance.eval()-.08)/.52)) if PART and b.par.Viewingmode.eval()=='object' and b.par.Exploding else 1
    off=[v*(f-1) for v in OFFSET]
    axes=[(SIZE,0,0),(-SIZE,0,0),(0,SIZE,0),(0,-SIZE,0),(0,0,SIZE),(0,0,-SIZE)]
    triangles=[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]
    for p,c in zip(POINTS,COLORS):
        for tri in triangles:
            poly=scriptOp.appendPoly(3,closed=True,addPoints=True)
            for v,i in zip(poly,tri):
                v.point.P=tuple(p[k]+axes[i][k]+off[k] for k in range(3));v.point.Cd=(*c,1)
'''
for key in ['body','stem','leaf']:
    cb=b.op(key+'/pointcloud_callbacks');offset=[centers[key][k]-center[k] for k in range(3)]
    cb.text=template%(d['parts'][key],d['colors'][key],.008,offset,True)
    mat=b.op(key+'_glow');mat.par.colorr=1;mat.par.colorg=1;mat.par.colorb=1
    b.op(key+'/pointcloud').cook(force=True)
ge=b.op('fuji_environment') or b.create(geometryCOMP,'fuji_environment')
for child in ge.children:child.destroy()
mat=b.op('fuji_environment_mat') or b.create(constantMAT,'fuji_environment_mat');mat.par.colorr=1;mat.par.colorg=1;mat.par.colorb=1;ge.par.material=mat;ge.par.rx=-90
cb=ge.create(textDAT,'callbacks');cb.text=template%(d['environment'],d['environment_colors'],.016,[0,0,0],False)
sop=ge.create(scriptSOP,'points');sop.par.callbacks=cb;sop.display=True;sop.render=True
b.op('render').par.geometry='body stem leaf fuji_environment'
c=b.op('observer');c.par.tx=5;c.par.ty=3.1;c.par.tz=7.5;c.par.ry=math.degrees(math.atan2(5,8.5));c.par.rx=-math.degrees(math.atan2(1.7,math.hypot(5,8.5)));c.par.fov=53.1
b.op('README').text='FUJI / AUDI A1 • Reference-inspired procedural point cloud. Body, wheels and glass support camera tracking and explosion. Not manufacturer CAD or a surveyed track.'
b.op('OUT').cook(force=True)
print('FUJI scene errors:',[(o.path,o.errors()) for o in b.findChildren() if o.errors()])
b.op('OUT').save(str(ROOT/'touchdesigner/FujiA1-preview.png'))
b.save(str(ROOT/'touchdesigner/FujiA1.tox'))
project.save(str(ROOT/'touchdesigner/FujiA1.toe'))
