import json,math
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
b=op('/project1/cyber_apple');m=b.op('tracker_runtime').module
m.pause()
# Validate the packet-to-camera path independently of how long a human holds a gesture.
controller=b.op('camera_controller').module
b.par.Tracking=True;b.par.Viewingmode='object';m.calibrate()
initial=m.camera_values()
for d in [{'Grip':True,'HandX':.1,'HandY':.2},{'Grip':True,'HandX':.3,'HandY':.3}]:m.packet(d);controller.updateCamera(0)
assert sum((a-z)**2 for a,z in zip(initial[:3],m.camera_values()[:3]))>.01
m.packet({'Explode':True,'FingerDistance':.6});controller.updateCamera(0)
for name in ['body','stem','leaf']:b.op(name+'/pointcloud').cook(force=True)
assert b.par.Exploding.eval()
m.stop()
b.par.Viewingmode='space';b.par.Demo=False
m.restore([0,2.2,6.5,-18.7,0])
# A stopped project contains only a blank preview texture.
preview=b.op('preview_callbacks').module;preview._last[:,:,:3]=0;b.op('tracking_preview').cook(force=True)
errors=[(n.path,n.errors()) for n in b.findChildren() if n.errors()]
assert not errors,errors
report=json.loads((ROOT/'touchdesigner/live-verification.json').read_text(encoding='utf-8'));report.update(native_panel=True,native_preview_size=[b.op('tracking_preview').width,b.op('tracking_preview').height],grip_packet_control=True,explosion_packet_control=True,node_errors=errors)
(ROOT/'touchdesigner/live-verification.json').write_text(json.dumps(report),encoding='utf-8')
b.save(str(ROOT/'touchdesigner/CyberApple.tox'))
project.save(str(ROOT/'touchdesigner/CyberApple.toe'))
print(report)
