bl_info={'name':'裸視3D / Cyber Apple','author':'NakedEye3D','version':(0,2,0),'blender':(4,0,0),'location':'View3D > Sidebar > 裸視3D','category':'3D View'}
import bpy,json,socket,time,subprocess,math
from bpy.app.handlers import persistent
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
RUNTIME=ROOT/'runtime/blender'
_state={}

def control(paused=None,stop=False):
    RUNTIME.mkdir(parents=True,exist_ok=True)
    scene=_state.get('scene',bpy.context.scene)
    d={'heartbeat':time.time(),'camera':scene.ne3d_camera,'mode':scene.ne3d_mode,'paused':_state.get('paused',True) if paused is None else paused,'stop':stop,'calibration':_state.get('calibration',0)}
    p=RUNTIME/'control.tmp';p.write_text(json.dumps(d));p.replace(RUNTIME/'control.json')

def capture(cam):return (cam.matrix_world.copy(),cam.data.shift_x,cam.data.shift_y,cam.data.lens)
def restore(cam,v):cam.matrix_world=v[0];cam.data.shift_x=v[1];cam.data.shift_y=v[2];cam.data.lens=v[3]
def apply_packet(d):
    cam=_state['cam'];scene=_state['scene'];base=_state['base'];target=_state['target'];distance=max(.1,(base.translation-target).length)
    if d.get('Explode') and scene.ne3d_mode=='object':
        factor=1+2*max(0,min(1,(d.get('FingerDistance',.08)-.08)/.52))
        parts=_state['parts'];center=_state['center']
        for o,pos in parts:o.location=center+(pos-center)*factor
        radius=max(((o.matrix_world@Vector(c))-center).length for o,_ in parts for c in o.bound_box) if parts else 1
        distance=max(_state['distance'],radius/max(.1,math.sin(min(cam.data.angle_x,cam.data.angle_y)/2))*1.15)
        cam.matrix_world=base.copy();cam.location=target+(base.translation-target).normalized()*distance
        _state['gesture']='explode';return
    if d.get('Grip') and scene.ne3d_mode=='object':
        hand=(d.get('HandX',0),d.get('HandY',0))
        if _state.get('gesture')!='grip':_state['hand']=hand;_state['gripbase']=cam.matrix_world.copy()
        start=_state['hand'];m=_state['gripbase'];yaw=Quaternion(Vector((0,0,1)),(hand[0]-start[0])*math.pi*1.4);pitch=Quaternion(m.to_quaternion()@Vector((1,0,0)),(hand[1]-start[1])*math.pi)
        q=yaw@pitch;cam.location=target+q@(m.translation-target);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();_state['gesture']='grip';return
    if _state.pop('gesture',None):_state['base']=cam.matrix_world.copy();base=_state['base']
    wave=d.get('WaveId',0)
    if scene.ne3d_mode=='space' and wave and wave!=_state.get('wave'):
        q=Quaternion(Vector((0,0,1)),d.get('WaveDirection',1)*math.pi/2);cam.location=target+q@(base.translation-target);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();_state['base']=cam.matrix_world.copy();base=_state['base'];_state['wave']=wave
    if d.get('HeadValid',True):
        cam.matrix_world=base.copy();q=base.to_quaternion();x=d.get('X',0)*distance*.22;y=d.get('Y',0)*distance*.22;z=max(-.25,min(.5,d.get('Z',0)))*distance
        cam.location=base.translation+q@Vector((x,y,z));cam.data.shift_x=_state['original'][1]+x/max(distance,1e-4)*cam.data.lens/cam.data.sensor_width;cam.data.shift_y=_state['original'][2]+y/max(distance,1e-4)*cam.data.lens/cam.data.sensor_width

def tick():
    if not _state:return None
    try:
        if bpy.context.scene!=_state['scene']:
            stop();return None
        if _state.get('mode')!=_state['scene'].ne3d_mode:
            _state['base']=_state['cam'].matrix_world.copy();_state['calibration']=time.time();_state['mode']=_state['scene'].ne3d_mode;_state.pop('gesture',None)
        control()
        latest=None
        while True:
            try:latest=json.loads(_state['socket'].recv(65536))
            except BlockingIOError:break
        try:
            st=json.loads((RUNTIME/'status.json').read_text())
            if st.get('error') and st.get('time',0)>_state.get('calibration',0):_state['error']=st['message']
        except (OSError,ValueError):pass
        if latest and not _state['paused']:
            apply_packet(latest);_state['received']=time.time()
        for screen in bpy.data.screens:
            for a in screen.areas:
                if a.type=='VIEW_3D':a.tag_redraw()
    except Exception as e:_state['error']=str(e)
    return .033

class NE3D_Start(bpy.types.Operator):
    bl_idname='ne3d.start';bl_label='開始 / 繼續追蹤'
    def execute(self,context):
        if _state and _state.get('error'):
            stop()
        if _state:
            _state['paused']=False;_state['base']=_state['cam'].matrix_world.copy();_state['calibration']=time.time();control(False);return {'FINISHED'}
        missing=[str(p) for p in [ROOT/'.venv/bin/python',ROOT/'models/face_landmarker.task',ROOT/'models/hand_landmarker.task'] if not p.exists()]
        if missing:self.report({'ERROR'},'找不到追蹤套件或模型：'+missing[0]);return {'CANCELLED'}
        cam=context.scene.camera
        if not cam:self.report({'ERROR'},'請先指定場景攝影機');return {'CANCELLED'}
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:sock.bind(('127.0.0.1',39549))
        except OSError as e:self.report({'ERROR'},str(e));sock.close();return {'CANCELLED'}
        sock.setblocking(False)
        parts=[(o,o.location.copy()) for o in context.scene.objects if o.get('nakedeye_part')]
        center=sum((p for _,p in parts),Vector())/len(parts) if parts else Vector()
        target=center if parts else cam.location+cam.rotation_euler.to_quaternion()@Vector((0,0,-5))
        _state.update(cam=cam,scene=context.scene,socket=sock,paused=False,original=capture(cam),base=cam.matrix_world.copy(),target=target,parts=parts,center=center,distance=(cam.location-target).length,calibration=time.time())
        control(False)
        subprocess.Popen(['/usr/bin/open','-n','-a',str(ROOT/'tools/NakedEye3D Webcam.app'),'--args','--client','blender'])
        
        if not bpy.app.timers.is_registered(tick):bpy.app.timers.register(tick)
        return {'FINISHED'}
class NE3D_Pause(bpy.types.Operator):
    bl_idname='ne3d.pause';bl_label='暫停追蹤'
    def execute(self,context):
        if _state:_state['paused']=True;control(True)
        return {'FINISHED'}
class NE3D_Stop(bpy.types.Operator):
    bl_idname='ne3d.stop';bl_label='停止並恢復'
    def execute(self,context):
        stop();return {'FINISHED'}
def stop():
    if bpy.app.timers.is_registered(tick):bpy.app.timers.unregister(tick)
    if _state:
        control(True,True);restore(_state['cam'],_state['original'])
        for o,pos in _state['parts']:o.location=pos
        _state['socket'].close();_state.clear()
class NE3D_Calibrate(bpy.types.Operator):
    bl_idname='ne3d.calibrate';bl_label='以目前視角重新校正'
    def execute(self,context):
        if _state:_state['base']=_state['cam'].matrix_world.copy();_state['calibration']=time.time();control()
        return {'FINISHED'}
class NE3D_Preview(bpy.types.Operator):
    bl_idname='ne3d.preview';bl_label='顯示 Webcam 預覽'
    def execute(self,context):
        bpy.ops.wm.url_open(url='http://127.0.0.1:39550/view');return {'FINISHED'}
class NE3D_Panel(bpy.types.Panel):
    bl_label='裸視3D';bl_idname='NE3D_PT_tracking';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='裸視3D'
    def draw(self,context):
        l=self.layout;l.prop(context.scene,'ne3d_mode',text='觀看模式');l.prop(context.scene,'ne3d_camera',text='Webcam');l.operator('ne3d.start');l.operator('ne3d.pause');l.operator('ne3d.stop');l.operator('ne3d.calibrate');l.operator('ne3d.preview')
        
        status=''
        try:status=json.loads((RUNTIME/'status.json').read_text()).get('message','')
        except (OSError,ValueError):pass
        l.label(text=_state.get('error',status or ('追蹤中' if _state and not _state['paused'] else '已暫停')))
        if _state and time.time()-_state.get('received',0)>2:l.label(text='等待 webcam 資料')
        l.label(text='先停止 Rhino 追蹤以釋放 webcam')
classes=(NE3D_Start,NE3D_Pause,NE3D_Stop,NE3D_Calibrate,NE3D_Preview,NE3D_Panel)
@persistent
def before_load(dummy):
    stop()
def register():
    for c in classes:bpy.utils.register_class(c)
    if before_load not in bpy.app.handlers.load_pre:bpy.app.handlers.load_pre.append(before_load)
    bpy.types.Scene.ne3d_mode=bpy.props.EnumProperty(items=[('space','空間模式','頭部視差與揮手90度'),('object','物體模式','三指抓握旋轉與雙食指爆炸圖')],default='space')
    bpy.types.Scene.ne3d_camera=bpy.props.IntProperty(default=0,min=0,max=8)
def unregister():
    stop()
    if before_load in bpy.app.handlers.load_pre:bpy.app.handlers.load_pre.remove(before_load)
    for c in reversed(classes):bpy.utils.unregister_class(c)
    del bpy.types.Scene.ne3d_mode;del bpy.types.Scene.ne3d_camera
