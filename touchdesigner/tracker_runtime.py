"""Embedded in a Text DAT by setup_tracking.py; inference runs locally."""
import json,socket,time,subprocess,math
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D');RUNTIME=ROOT/'runtime/touchdesigner'
_state={}
def base():return me.parent()
def message(text):base().par.Status=text

def write_control(paused=False,stop=False):
    b=base();RUNTIME.mkdir(parents=True,exist_ok=True)
    data={'heartbeat':time.time(),'camera':int(b.par.Camera),'mode':b.par.Viewingmode.eval(),'paused':paused,'stop':stop,'calibration':_state.get('calibration',0)}
    p=RUNTIME/'control.tmp';p.write_text(json.dumps(data),encoding='utf-8');p.replace(RUNTIME/'control.json')

def camera_values():
    c=base().op('observer');return [c.par.tx.eval(),c.par.ty.eval(),c.par.tz.eval(),c.par.rx.eval(),c.par.ry.eval()]
def restore(values):
    c=base().op('observer')
    for name,value in zip(['tx','ty','tz','rx','ry'],values):setattr(c.par,name,value)

def calibrate():
    _state['calibration']=time.time();b=base();b.store('state',{'active':True,'base':camera_values(),'origin':_state.get('original',camera_values()),'hand':None})
    b.par.Headx=0;b.par.Heady=0;b.par.Headz=0;b.par.Grabbing=False;b.par.Exploding=False
    if _state:write_control(_state.get('paused',False))

def start():
    b=base();b.par.Demo=False
    if _state.get('error'):stop()
    if _state:
        _state['paused']=False;b.par.Tracking=True;calibrate();message('等待 webcam 資料');return
    missing=[str(p) for p in [ROOT/'.venv/bin/python',ROOT/'models/face_landmarker.task',ROOT/'models/hand_landmarker.task'] if not p.exists()]
    if missing:b.par.Tracking=False;message('缺少套件或模型：'+missing[0]);return
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:s.bind(('127.0.0.1',39559))
    except OSError as e:s.close();b.par.Tracking=False;message('追蹤通道被占用：'+str(e));return
    s.setblocking(False);_state.update(socket=s,original=camera_values(),paused=False,mode=b.par.Viewingmode.eval(),calibration=time.time(),started=time.time())
    calibrate();b.par.Tracking=True
    subprocess.Popen(['/usr/bin/open','-n','-a',str(ROOT/'tools/NakedEye3D Webcam.app'),'--args','--client','touchdesigner'])
    message('正在啟動 webcam')

def pause():
    if _state:_state['paused']=True;write_control(True)
    base().par.Tracking=False;message('已暫停；webcam 預覽持續')

def stop():
    b=base()
    if _state:
        write_control(True,True);_state['socket'].close();restore(_state['original']);_state.clear()
    b.par.Tracking=False;b.par.Grabbing=False;b.par.Exploding=False;b.par.Headx=0;b.par.Heady=0;b.par.Headz=0;b.unstore('state');message('已停止；webcam 已釋放')

def packet(d):
    b=base();obj=b.par.Viewingmode.eval()=='object'
    b.par.Exploding=obj and d.get('Explode',False);b.par.Grabbing=obj and d.get('Grip',False) and not b.par.Exploding
    b.par.Handx=d.get('HandX',0);b.par.Handy=d.get('HandY',0);b.par.Fingerdistance=d.get('FingerDistance',.08)
    if not obj and d.get('WaveId',0) and d['WaveId']!=_state.get('wave'):
        state=b.fetch('state',{});m=state.get('base',camera_values());a=d.get('WaveDirection',1)*math.pi/2
        x,y,z,rx,ry=m;state['base']=[x*math.cos(a)+z*math.sin(a),y,z*math.cos(a)-x*math.sin(a),rx,ry+a*180/math.pi];b.store('state',state);_state['wave']=d['WaveId']
    if not b.par.Grabbing and not b.par.Exploding:
        if d.get('HeadValid',True):b.par.Headx=d.get('X',0);b.par.Heady=d.get('Y',0);b.par.Headz=d.get('Z',0)
        else:return False
    return True

def tick():
    b=base()
    if b.par.Tracking and not _state:start()
    if not _state:return False
    if not b.par.Tracking and not _state.get('paused'):pause()
    if b.par.Tracking and _state.get('paused'):start()
    if _state.get('mode')!=b.par.Viewingmode.eval():_state['mode']=b.par.Viewingmode.eval();calibrate()
    write_control(_state.get('paused',False))
    if time.time()-_state.get('preview_time',0)>.15:
        b.op('tracking_preview').cook(force=True);_state['preview_time']=time.time()
    latest=None
    while True:
        try:latest=json.loads(_state['socket'].recv(65536))
        except BlockingIOError:break
        except (OSError,ValueError):break
    try:
        st=json.loads((RUNTIME/'status.json').read_text(encoding='utf-8'))
        if st.get('time',0)>_state.get('started',0):
            message(st.get('message',''))
            if st.get('error'):_state['error']=st['message'];b.par.Tracking=False;_state['paused']=True
    except (OSError,ValueError):pass
    if latest:
        _state['received']=time.time();_state['head_valid']=latest.get('HeadValid',True)
    return bool(latest and not _state.get('paused') and packet(latest))
