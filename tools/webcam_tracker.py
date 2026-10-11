"""Local webcam inference; only landmark-derived coordinates leave this process."""
import json
import math
import os
from pathlib import Path
import socket
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageSequence
from hand_gestures import index_only, three_finger_grasp, palm_pose, palm_openness, palm_scale

ROOT = Path(__file__).resolve().parents[1]
import argparse
_parser=argparse.ArgumentParser()
_parser.add_argument('--client',default='rhino',choices=['rhino'])
_args=_parser.parse_args()
PORT=39539
PREVIEW_PORT=PORT+1
RUNTIME = ROOT / 'runtime'
RUNTIME.mkdir(parents=True,exist_ok=True)
preview = b''
preview_rgba = b''

class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/view'):
            data=b"<html><body style='margin:0;background:#191919'><img id='cam' width='224' height='168'><script>setInterval(()=>document.getElementById('cam').src='/?t='+Date.now(),150)</script></body></html>"
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data);return
        raw=self.path.startswith('/rgba')
        data = preview_rgba if raw else preview
        self.send_response(200 if data else 204)
        self.send_header('Content-Type','application/octet-stream' if raw else 'image/jpeg')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        if data: self.wfile.write(data)
    def log_message(self,*args): pass

def render_preview(frame, faces, hands, cover, object_mode=False, gripping=False, active_index=0):
    global preview, preview_rgba
    display = cv2.flip(frame,1)
    h,w = display.shape[:2]
    def pixel(p): return (int((1-p.x)*w),int(p.y*h))
    if not faces.face_landmarks:
        display[:] = 25
        cv2.putText(display,'Waiting for face - preview hidden',(35,h//2),cv2.FONT_HERSHEY_SIMPLEX,.65,(220,220,220),2)
    for points in faces.face_landmarks:
        # Eye centers, rather than face bounds, anchor the logo precisely.
        eyes=[]
        for outer,inner in [(33,133),(263,362)]:
            p,q=points[outer],points[inner]
            eyes.append(np.array([(1-(p.x+q.x)/2)*w,(p.y+q.y)/2*h],dtype=np.float32))
        eyes.sort(key=lambda p:p[0])
        source=np.array([[188.,247.],[297.,247.]],dtype=np.float32)
        delta=eyes[1]-eyes[0]
        if np.linalg.norm(delta)<4: continue
        # Third point makes a similarity transform: scale + roll + translation.
        target=np.array([eyes[0],eyes[1],eyes[0]+np.array([-delta[1],delta[0]])],dtype=np.float32)
        src=np.array([source[0],source[1],source[0]+[0.,109.]],dtype=np.float32)
        matrix=cv2.getAffineTransform(src,target)
        alpha=cover[:,:,3:4].astype(np.float32)/255. if cover.shape[2]==4 else np.ones((*cover.shape[:2],1),dtype=np.float32)
        premultiplied=cover[:,:,:3].astype(np.float32)*alpha
        warped_color=cv2.warpAffine(premultiplied,matrix,(w,h))
        warped_alpha=cv2.warpAffine(alpha,matrix,(w,h))[:,:,None]
        display=(warped_color+display*(1-warped_alpha)).clip(0,255).astype(np.uint8)
    connections=[(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]
    for hand_index,points in enumerate(hands.hand_landmarks):
        for a,b in connections: cv2.line(display,pixel(points[a]),pixel(points[b]),(80,220,80),2)
        for p in points: cv2.circle(display,pixel(p),3,(80,255,80),-1)
        if object_mode:
            center=np.mean([pixel(points[i]) for i in [0,5,9,13,17]],axis=0).astype(int)
            color=(40,220,40) if gripping and hand_index==active_index else (40,40,230)
            cv2.circle(display,tuple(center),18,color,-1,cv2.LINE_AA)
            cv2.circle(display,tuple(center-np.array([5,5])),5,(220,255,220) if color[1]>100 else (220,220,255),-1,cv2.LINE_AA)
        else:
            cv2.circle(display,pixel(points[9]),8,(255,160,60),2)
    display=cv2.resize(display,(224,168))
    preview_rgba=cv2.cvtColor(display,cv2.COLOR_BGR2RGBA).tobytes()
    ok,encoded=cv2.imencode('.jpg',display,[cv2.IMWRITE_JPEG_QUALITY,75])
    if ok:
        preview=encoded.tobytes()
        target=RUNTIME / "preview.jpg"
        temp=RUNTIME / "preview.tmp"
        temp.write_bytes(preview)
        temp.replace(target)

def status(message, **extra):
    target = RUNTIME / 'status.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(dict(message=message, time=time.time(), **extra)))
    temp.replace(target)

def control():
    try:
        return json.loads((RUNTIME / 'control.json').read_text())
    except (OSError, ValueError):
        return {'paused': True}

def main():
    camera_lock=open(ROOT/'runtime/camera.lock','a+b')
    if camera_lock.seek(0,2)==0:camera_lock.write(b'0');camera_lock.flush()
    for attempt in range(16):
        try:
            if os.name=='nt':
                import msvcrt
                camera_lock.seek(0);msvcrt.locking(camera_lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(camera_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            break
        except OSError:
            if attempt==15:raise RuntimeError('Webcam 已由另一套軟體使用；請先按停止，再重新開始')
            time.sleep(.1)
    for attempt in range(20):
        try:
            server=ThreadingHTTPServer(('127.0.0.1',PREVIEW_PORT),PreviewHandler)
            break
        except OSError as error:
            if error.errno not in (48,98,10048) or attempt==19: raise
            time.sleep(.1)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    covers=[]; durations=[]
    with Image.open(ROOT/'assets/face-cover.gif') as animation:
        for frame in ImageSequence.Iterator(animation):
            covers.append(cv2.cvtColor(np.array(frame.convert('RGBA')),cv2.COLOR_RGBA2BGRA))
            durations.append(max(.02,frame.info.get('duration',40)/1000.))
    animation_started=time.monotonic()
    animation_length=sum(durations)
    status('正在載入追蹤模型')
    vision = mp.tasks.vision
    base = mp.tasks.BaseOptions
    face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=base(model_asset_path=str(ROOT/'models/face_landmarker.task')),
        running_mode=vision.RunningMode.VIDEO, num_faces=4))
    hand = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=base(model_asset_path=str(ROOT/'models/hand_landmarker.task')),
        running_mode=vision.RunningMode.VIDEO, num_hands=2))
    camera = cv2.VideoCapture(int(control().get('camera',0)), cv2.CAP_DSHOW if os.name=='nt' else cv2.CAP_AVFOUNDATION)
    if not camera.isOpened():
        raise RuntimeError('無法開啟 webcam，請檢查相機權限或相機是否被占用')
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    baseline = None; smooth = [0.,0.,0.]; calibration = None
    frames = 0; stable_since = None; grip = False; grip_release_since = None; last_face = time.monotonic(); report = 0
    previous_grip=False; active_side=None; mode='space'; explode_since=None; previous_explode=False
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sender:
        try:
            while True:
                if os.getppid() == 1: break
                settings = control()
                if settings.get('stop'): break
                if time.time()-settings.get('heartbeat',time.time()) > 30: break
                ok, frame = camera.read()
                if not ok: raise RuntimeError('webcam 影像讀取失敗')
                frames += 1
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
                stamp = int(time.monotonic()*1000)
                faces = face.detect_for_video(image,stamp)
                mirrored=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(cv2.flip(frame,1),cv2.COLOR_BGR2RGB))
                hands = hand.detect_for_video(mirrored,stamp)
                for landmarks in hands.hand_landmarks:
                    for landmark in landmarks: landmark.x=1-landmark.x
                elapsed=(time.monotonic()-animation_started)%animation_length
                index=0
                while index<len(durations)-1 and elapsed>=durations[index]:
                    elapsed-=durations[index]; index+=1
                object_mode=settings.get('mode','space')=='object'
                hx=hy=hand_size=0.; active_index=0
                sides={categories[0].category_name for categories in hands.handedness if categories[0].score>.65}
                explosion_candidate=object_mode and sides=={'Left','Right'} and len(hands.hand_landmarks)==2 and all(index_only(p) for p in hands.hand_landmarks)
                palm_mode=settings.get('explosion_method','two_index')=='palm'
                pose=palm_pose(hands.hand_landmarks[0]) if palm_mode and len(hands.hand_landmarks)==1 else None
                if palm_mode: explosion_candidate=object_mode and len(hands.hand_landmarks)==1 and (pose=='open' or (previous_explode and pose!='fist'))
                if hands.hand_landmarks:
                    if active_side:
                        found=[i for i,c in enumerate(hands.handedness) if c[0].category_name==active_side]
                        if found: active_index=found[0]
                        else: grip=False; active_side=None; stable_since=None
                    if not active_side:
                        qualifying=[i for i,p in enumerate(hands.hand_landmarks) if three_finger_grasp(p)]
                        if qualifying: active_index=qualifying[0]
                    p=hands.hand_landmarks[active_index]
                    candidate=three_finger_grasp(p,active=grip) and not explosion_candidate and pose!='fist'
                    if candidate and object_mode and not settings.get('paused'):
                        grip_release_since=None
                        if stable_since is None: stable_since=time.monotonic()
                        if time.monotonic()-stable_since>.12:
                            grip=True
                            active_side=hands.handedness[active_index][0].category_name
                    else:
                        # Brief landmark jitter must not drop/re-anchor a grab.
                        if grip_release_since is None: grip_release_since=time.monotonic()
                        if not grip or explosion_candidate or not object_mode or settings.get('paused') or time.monotonic()-grip_release_since>.18:
                            grip=False; stable_since=None; active_side=None
                    hand_size=palm_scale(p)
                    hx=-sum(p[i].x for i in [0,5,9,13,17])/5
                    hy=-sum(p[i].y for i in [0,5,9,13,17])/5
                else: grip=False; stable_since=None; active_side=None
                finger_distance=0.;explode=False
                sides={categories[0].category_name for categories in hands.handedness if categories[0].score>.65}
                if explosion_candidate:
                    if explode_since is None: explode_since=time.monotonic()
                    explode=time.monotonic()-explode_since>.15 and not settings.get('paused')
                    if palm_mode: finger_distance=.08+.52*palm_openness(hands.hand_landmarks[0])
                    else:
                        a,b=[p[8] for p in hands.hand_landmarks]
                        finger_distance=math.hypot(a.x-b.x,a.y-b.y)
                else: explode_since=None
                if explode: grip=False;stable_since=None;active_side=None
                if previous_explode and not explode: baseline=None;smooth=[0.,0.,0.]
                previous_explode=explode
                if previous_grip and not grip:
                    baseline=None; smooth=[0.,0.,0.]
                previous_grip=grip
                render_preview(frame,faces,hands,covers[index],object_mode,grip,active_index)
                if settings.get('paused'):
                    grip=False; stable_since=None
                    if time.monotonic()-report>.25:
                        status('已暫停追蹤（預覽持續）',frames=frames); report=time.monotonic()
                    continue
                if calibration != settings.get('calibration'):
                    baseline = None; calibration = settings.get('calibration'); smooth = [0.,0.,0.]
                if not faces.face_landmarks and not grip and not explode:
                    if time.monotonic()-report>.25:
                        status('未偵測到臉部，視角保持不動',frames=frames); report=time.monotonic()
                    # Explicitly release camera grabbing even when the face is absent.
                    sender.sendto(json.dumps(dict(X=0,Y=0,Z=0,Grip=False,HeadValid=False,SmoothReturn=palm_mode,HandValid=bool(hands.hand_landmarks),Mode=settings.get('mode','space'))).encode(),('127.0.0.1',PORT))
                    continue
                depth=1.
                if not grip and not explode:
                    points=faces.face_landmarks[0]
                    a,b=points[33],points[263]
                    current=((a.x+b.x)/2,(a.y+b.y)/2,math.hypot(a.x-b.x,a.y-b.y))
                    if baseline is None: baseline=current
                    depth=baseline[2]/max(current[2],.001)
                    raw=[-(current[0]-baseline[0])*.8,-(current[1]-baseline[1])*.8,depth-1]
                    for i in range(3):
                        lower,upper=(-.25,.5) if i==2 else (-.3,.3)
                        smooth[i]+=min(.9,(.4 if i==2 else .25)*max(.2,min(3.,float(settings.get('sensitivity',1.)))))*(max(lower,min(upper,raw[i]))-smooth[i])
                data=dict(SmoothReturn=palm_mode,HandValid=bool(hands.hand_landmarks),X=smooth[0],Y=smooth[1],Z=smooth[2],Grip=grip,HandX=hx,HandY=hy,HandSize=hand_size,Mode=settings.get('mode','space'),Explode=explode,FingerDistance=finger_distance)
                sender.sendto(json.dumps(data).encode(),('127.0.0.1',PORT))
                if time.monotonic()-report > .25:
                    status('雙食指：爆炸圖' if explode else ('三指抓握：攝影機旋轉（頭部控制暫停）' if grip else '頭部追蹤中'),frames=frames,hand=bool(hands.hand_landmarks),depth=round(depth,2),sides=list(sides))
                    report=time.monotonic()
        finally:
            camera.release(); face.close(); hand.close()
            server.shutdown(); server.server_close()
    status('已停止，webcam 已釋放')

if __name__ == '__main__':
    try: main()
    except Exception as error:
        status(str(error), error=True)
        raise
