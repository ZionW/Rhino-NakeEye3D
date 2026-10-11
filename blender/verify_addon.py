import bpy,importlib.util,sys,math
from mathutils import Vector
old=getattr(bpy.types,'NE3D_PT_tracking',None)
if old:old.draw.__globals__['unregister']()
spec=importlib.util.spec_from_file_location('nakedeye3d','/Users/zionw/Desktop/Codex/裸視3D/blender/nakedeye3d/__init__.py');addon=importlib.util.module_from_spec(spec);sys.modules['nakedeye3d']=addon;spec.loader.exec_module(addon);addon.register()
scene=bpy.context.scene;cam=scene.camera;original=addon.capture(cam);parts=[(o,o.location.copy()) for o in scene.objects if o.get('nakedeye_part')];center=sum((p for _,p in parts),Vector())/len(parts)
addon._state.update(cam=cam,scene=scene,base=cam.matrix_world.copy(),original=original,target=center,parts=parts,center=center,distance=(cam.location-center).length)
base_distance=(cam.location-center).length;scene.ne3d_mode='space'
addon.apply_packet({'Z':-.2});assert (cam.location-center).length<base_distance
assert cam.data.lens==original[3]
addon.restore(cam,original);addon.apply_packet({'WaveId':1,'WaveDirection':1,'HeadValid':False});assert abs((cam.location-center).length-base_distance)<1e-4
rotated=cam.location.copy();addon.apply_packet({'WaveId':1,'WaveDirection':1,'HeadValid':False});assert (cam.location-rotated).length<1e-5
addon.restore(cam,original);addon._state['base']=original[0].copy();scene.ne3d_mode='object'
addon.apply_packet({'Explode':True,'FingerDistance':.6});assert any((o.location-p).length>.1 for o,p in parts)
large=(cam.location-center).length;addon.apply_packet({'Explode':True,'FingerDistance':.08});assert (cam.location-center).length<=large
addon.apply_packet({'Grip':True,'HandX':0,'HandY':0});addon.apply_packet({'Grip':True,'HandX':.2,'HandY':.1});assert (cam.location-original[0].translation).length>.1
addon.restore(cam,original)
for o,p in parts:o.location=p
addon._state.clear();scene.ne3d_mode='space'
result={'head_forward':True,'fixed_lens':True,'wave_once':True,'explosion_limit_and_fit':True,'grip_orbit':True,'restore':True}
import json
open('/Users/zionw/Desktop/Codex/裸視3D/blender/verification.json','w').write(json.dumps(result))
