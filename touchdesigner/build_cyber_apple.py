"""Paste/run in a TouchDesigner Text DAT. Creates a self-contained Base COMP.
Native TD nodes only; camera controls are custom parameters, no external webcam tracker.
"""
import json, math
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
data=json.loads((ROOT/'demos/cyberspace.json').read_text(encoding='utf-8'))
base=op('/project1').create(baseCOMP,'cyber_apple')
page=base.appendCustomPage('裸視3D')
mode=page.appendMenu('Viewingmode',label='觀看模式')[0];mode.menuNames=['space','object'];mode.menuLabels=['空間模式','物體模式']
for name,label,default in [('Tracking','執行追蹤控制',False),('Demo','自動導覽示範',True),('Grabbing','三指抓握',False),('Exploding','雙食指爆炸圖',False)]:
    p=page.appendToggle(name,label=label)[0];p.val=default
for name,label,value,lo,hi in [('Headx','頭部左右',0,-1,1),('Heady','頭部上下',0,-1,1),('Headz','頭部遠近',0,-.25,.5),('Handx','手部左右',0,-1,1),('Handy','手部上下',0,-1,1),('Fingerdistance','雙指距離',.08,.08,.6)]:
    p=page.appendFloat(name,label=label)[0];p.val=value;p.min=lo;p.max=hi;p.clampMin=True;p.clampMax=True
# Mesh dots are explicit octahedra: reliable on both Metal/Vulkan and older TD.
callback_template='''POINTS = %r
SIZE = %r
OFFSET = %r
PART = %r
import math
def onCook(scriptOp):
    scriptOp.clear()
    root=scriptOp.parent(2)
    f=1+2*max(0,min(1,(root.par.Fingerdistance.eval()-.08)/.52)) if root.par.Viewingmode.eval()=='object' and root.par.Exploding else 1
    off=[a*(f-1) for a in OFFSET]
    axes=[(SIZE,0,0),(-SIZE,0,0),(0,SIZE,0),(0,-SIZE,0),(0,0,SIZE),(0,0,-SIZE)]
    triangles=[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]
    for p in POINTS:
        for tri in triangles:
            poly=scriptOp.appendPoly(3,closed=True,addPoints=True)
            for v,i in zip(poly,tri):v.point.P=tuple(p[k]+axes[i][k]+off[k] for k in range(3))
    return
'''
centers=[]
for key,points in data['parts'].items():centers.append([sum(p[k] for p in points)/len(points) for k in range(3)])
center=[sum(p[k] for p in centers)/3 for k in range(3)]
colors={'body':(1,.55,.035),'stem':(1,.85,.3),'leaf':(1,.75,.15),'network':(.32,.10,.008)}
for index,(key,points) in enumerate(list(data['parts'].items())+[('network',data['nodes'])]):
    geo=base.create(geometryCOMP,key);geo.nodeX=index*220;geo.nodeY=0
    for child in geo.children:child.destroy()
    mat=base.create(constantMAT,key+'_glow');mat.par.colorr,mat.par.colorg,mat.par.colorb=colors[key];geo.par.material=mat
    offset=[centers[index][k]-center[k] for k in range(3)] if key!='network' else [0,0,0]
    cb=geo.create(textDAT,'pointcloud_callbacks');cb.text=callback_template%(points[::2] if key!='network' else points,.009 if key!='network' else .026,offset,key)
    sop=geo.create(scriptSOP,'pointcloud');sop.par.callbacks=cb;sop.display=True;sop.render=True
# Open polyline network + scanner rings + ground grid.
segments=list(data['edges'])
for i in range(-10,11):
    v=i*.5;segments.extend([[[-5,v,-1.4],[5,v,-1.4]],[[v,-5,-1.4],[v,5,-1.4]]])
for r in [1.45,1.65,2.1]:segments.append([[r*math.cos(a*math.tau/180),r*math.sin(a*math.tau/180),-1.28] for a in range(181)])
grid=base.create(geometryCOMP,'network_lines')
for child in grid.children:child.destroy()
grid.par.material=base.op('network_glow')
cb=grid.create(textDAT,'line_callbacks');cb.text='SEGMENTS='+repr(segments)+'''\ndef onCook(scriptOp):
    scriptOp.clear()
    for segment in SEGMENTS:
        line=scriptOp.appendPoly(len(segment),closed=False,addPoints=True)
        for v,p in zip(line,segment):v.point.P=p
'''
sop=grid.create(scriptSOP,'lines');sop.par.callbacks=cb;sop.display=True;sop.render=True
amb=json.loads((ROOT/'demos/amber_space.json').read_text(encoding='utf-8'))
for key,color in [('gold',(.6,.22,.015)),('blue',(.02,.45,1)),('motes',(1,.8,.35))]:
    geo=base.create(geometryCOMP,'ambient_'+key)
    for child in geo.children:child.destroy()
    mat=base.create(constantMAT,key+'_mat');mat.par.colorr,mat.par.colorg,mat.par.colorb=color;geo.par.material=mat
    cb=geo.create(textDAT,'callbacks')
    if key=='motes':cb.text=callback_template%(amb[key],.017,[0,0,0],key)
    else:cb.text='SEGMENTS='+repr(amb[key])+'\n'+grid.op('line_callbacks').text.split('\n',1)[1]
    sop=geo.create(scriptSOP,'geometry');sop.par.callbacks=cb;sop.display=True;sop.render=True
cam=base.create(cameraCOMP,'observer');cam.par.tx=0;cam.par.ty=-6.5;cam.par.tz=2.2
# TD uses Y up; transform all geometry so common source Z-up becomes native Y-up.
for geo in base.findChildren(type=geometryCOMP,depth=1):geo.par.rx=-90
cam.par.tx=0;cam.par.ty=2.2;cam.par.tz=6.5;cam.par.rx=-18.7
render=base.create(renderTOP,'render');render.par.camera=cam;render.par.geometry='body stem leaf network network_lines ambient_gold ambient_blue ambient_motes';render.par.resolutionw=1280;render.par.resolutionh=720
out=base.create(nullTOP,'OUT');out.inputConnectors[0].connect(render);out.viewer=True
webcam=base.create(videodeviceinTOP,'webcam_preview');webcam.par.active=False
notes=base.create(textDAT,'README');notes.text='''CYBER APPLE / 裸視3D
右鍵 cyber_apple → Parameters → 裸視3D
Demo: 自動導覽。Tracking: 開始/暫停控制；開始瞬間保存 observer 數值。
空間模式: Headx/y/z。物體模式: Grabbing + Handx/y；Exploding + Fingerdistance。
手勢解除後保留新攝影機基準；爆炸距離上限為三倍，視圖自動容納物件。
webcam_preview 為 TD 內建攝影機輸入，預設關閉避免搶用 webcam。
此 macOS 示範不包含原生臉部/手指辨識；控制參數為追蹤接入點。
'''
execute=base.create(executeDAT,'camera_controller');execute.par.framestart=True
execute.text='''import math,time
from tdu import Position

def onFrameStart(frame):
    b=parent();c=b.op('observer');s=b.fetch('state',{})
    active=bool(b.par.Tracking)
    current=[c.par.tx.eval(),c.par.ty.eval(),c.par.tz.eval(),c.par.rx.eval(),c.par.ry.eval()]
    if active and not s.get('active'):
        s={'active':True,'base':current[:],'origin':current[:],'hand':None}
    if not active:
        s['active']=False
        if b.par.Demo:
            a=absTime.seconds*.14;c.par.tx=math.sin(a)*6.5;c.par.tz=math.cos(a)*6.5;c.par.ty=2.2;c.par.ry=a*180/math.pi;c.par.rx=-18.7
        b.store('state',s);return
    base=s['base'];obj=b.par.Viewingmode.eval()=='object'
    grip=obj and bool(b.par.Grabbing);explode=obj and bool(b.par.Exploding)
    if grip and not explode:
        if s.get('hand') is None:s['hand']=[b.par.Handx.eval(),b.par.Handy.eval(),current[:]]
        hx,hy,m=s['hand'];yaw=(b.par.Handx.eval()-hx)*math.pi*1.4
        pitch=(b.par.Handy.eval()-hy)*math.pi*.65
        radius=math.sqrt(sum(v*v for v in m[:3]));angle=math.atan2(m[0],m[2])+yaw;tilt=max(-1.2,min(1.2,math.asin(m[1]/radius)+pitch))
        c.par.tx=radius*math.cos(tilt)*math.sin(angle);c.par.ty=radius*math.sin(tilt);c.par.tz=radius*math.cos(tilt)*math.cos(angle);c.par.ry=angle*180/math.pi;c.par.rx=-tilt*180/math.pi
    else:
        if s.get('hand') is not None:s['hand']=None;s['base']=current[:];base=s['base']
        radius=math.sqrt(sum(v*v for v in base[:3]))
        scale=1
        if explode:
            f=1+2*max(0,min(1,(b.par.Fingerdistance.eval()-.08)/.52));scale=max(1,(1.8+f*.45)/(radius*math.sin(math.radians(c.par.fov.eval()/2)))*1.15)
        else:scale=1+max(-.25,min(.5,b.par.Headz.eval()))
        c.par.tx=base[0]*scale+(0 if explode else b.par.Headx.eval()*radius*.22);c.par.ty=base[1]*scale+(0 if explode else b.par.Heady.eval()*radius*.22);c.par.tz=base[2]*scale;c.par.rx=base[3];c.par.ry=base[4]
    b.store('state',s)
    return
'''
for i,node in enumerate(base.children):node.nodeX=(i%6)*220;node.nodeY=-(i//6)*160
SKIP_SAVE=True
exec(compile((ROOT/'touchdesigner/setup_tracking.py').read_text(encoding='utf-8'),'setup_tracking.py','exec'))
exec(compile((ROOT/'touchdesigner/build_control_panel.py').read_text(encoding='utf-8'),'build_control_panel.py','exec'))
exec(compile((ROOT/'touchdesigner/update_scan_style.py').read_text(encoding='utf-8'),'update_scan_style.py','exec'))
base.save(str(ROOT/'touchdesigner/CyberApple.tox'))
print('Created',base.path,'and saved CyberApple.tox')
