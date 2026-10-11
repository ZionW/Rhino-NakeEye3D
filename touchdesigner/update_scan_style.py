from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/cyber_apple')
style=(ROOT/'demos/scan_style.py').read_text(encoding='utf-8')
for key in ['body','stem','leaf']:
    cb=b.op(key+'/pointcloud_callbacks')
    if 'def scan_color' not in cb.text:
        s=cb.text.replace('scriptOp.clear()','scriptOp.clear()\n    scriptOp.pointAttribs.create(\'Cd\')')
        s=s.replace('v.point.P=tuple(p[k]+axes[i][k]+off[k] for k in range(3))','v.point.P=tuple(p[k]+axes[i][k]*.68+off[k] for k in range(3)); v.point.Cd=(*scan_color(p,PART),1)')
        cb.text=style+'\n'+s
    mat=b.op(key+'_glow');mat.par.colorr=1;mat.par.colorg=1;mat.par.colorb=1
    b.op(key+'/pointcloud').cook(force=True)
blur=b.op('scan_halo') or b.create(blurTOP,'scan_halo');blur.par.size=13;blur.inputConnectors[0].connect(b.op('render'))
mix=b.op('scan_light') or b.create(compositeTOP,'scan_light');mix.par.operand='add';mix.inputConnectors[0].connect(b.op('render'));mix.inputConnectors[1].connect(blur)
b.op('OUT').inputConnectors[0].connect(mix)
b.op('OUT').cook(force=True)
print('Scan errors:',[(o.path,o.errors()) for o in b.findChildren() if o.errors()])
b.op('OUT').save(str(ROOT/'touchdesigner/CyberApple-scan-preview.png'))
b.save(str(ROOT/'touchdesigner/CyberApple.tox'))
project.save(str(ROOT/'touchdesigner/CyberApple.toe'))
