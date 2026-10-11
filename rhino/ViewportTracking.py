import math
import time
import socket
import json
import Rhino
import importlib
import ExplodedView as exploded_module
importlib.reload(exploded_module)

class ViewportTracking:
    def __init__(self):
        self.socket=None
        self.view=None
        self.original=None
        self.basis=None
        self.strength=1.0
        self.sensitivity=1.0
        self.explosion_factor=3.0
        self.return_started=None
        self.grabbing=False
        self.mode='space'
        self.explosion=None
        self.exploding=False
        self.explosion_blocked=False

    def start(self,view):
        self.stop(False)
        self.view=view
        vp=view.ActiveViewport
        self.original=Rhino.DocObjects.ViewportInfo(vp)
        self.basis=Rhino.DocObjects.ViewportInfo(vp)
        self.basis.UnlockCamera()
        self.target=vp.CameraTarget
        self.distance=vp.CameraLocation.DistanceTo(self.target)
        if self.distance<=1e-6: raise RuntimeError('攝影機距離太小')
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1',39539))
        self.socket.setblocking(False)
        self.last_wave=0
        self.grabbing=False
        self.mode='space'
        self.explosion_blocked=False

    def stop(self,restore=True):
        self.return_started=None
        if self.explosion:
            self.explosion.restore();self.explosion=None;self.exploding=False
        if self.grabbing:
            self.grab_basis.Dispose(); self.grabbing=False
        if self.socket: self.socket.close(); self.socket=None
        if restore and self.view and self.original:
            self.view.ActiveViewport.SetViewProjection(self.original,False)
            self.view.Redraw()
        if self.original: self.original.Dispose()
        if self.basis: self.basis.Dispose()
        self.original=self.basis=None

    def pause(self):
        if self.socket: self.socket.close(); self.socket=None

    def reset_explosion(self):
        self.return_started=None
        if self.explosion:
            self.explosion.restore();self.explosion=None
            self.basis.Dispose()
            self.basis=Rhino.DocObjects.ViewportInfo(self.view.ActiveViewport)
            self.basis.UnlockCamera()
            self.target=self.view.ActiveViewport.CameraTarget
            self.distance=self.basis.CameraLocation.DistanceTo(self.target)
        self.exploding=False
        # Require release before the same held gesture may explode again.
        self.explosion_blocked=True

    def advance_return(self):
        elapsed=(time.monotonic()-self.return_started)/.7
        if self.explosion:self.explosion.return_step(elapsed)
        if elapsed>=1:
            self.reset_explosion()
        return True

    def update(self):
        if self.return_started is not None:
            self.advance_return();return
        if not self.socket: return
        data=None
        for _ in range(64):
            try: packet=self.socket.recv(2048)
            except BlockingIOError: break
            try: data=json.loads(packet)
            except ValueError: continue
        if not data: return
        values=[data.get(k,0)*self.strength for k in ('X','Y','Z')]
        if not all(math.isfinite(x) for x in values): return
        mode=data.get('Mode','space')
        if mode!=self.mode:
            if self.explosion:
                self.explosion.restore();self.explosion=None;self.exploding=False
            if self.grabbing: self.grab_basis.Dispose()
            self.basis.Dispose()
            self.basis=Rhino.DocObjects.ViewportInfo(self.view.ActiveViewport)
            self.basis.UnlockCamera()
            self.distance=self.basis.CameraLocation.DistanceTo(self.target)
            self.mode=mode; self.grabbing=False
            self.last_wave=data.get('WaveId',0)
            if mode=='object':
                selected=list(Rhino.RhinoDoc.ActiveDoc.Objects.GetSelectedObjects(False,False))
                if selected:
                    box=selected[0].Geometry.GetBoundingBox(True)
                    for obj in selected[1:]: box.Union(obj.Geometry.GetBoundingBox(True))
                    self.target=box.Center
                    self.distance=self.basis.CameraLocation.DistanceTo(self.target)
        explode=mode=='object' and data.get('Explode',False)
        if self.explosion_blocked:
            if explode:return
            self.explosion_blocked=False
        if explode:
            if self.grabbing: self.grab_basis.Dispose();self.grabbing=False
            if self.explosion is None:
                self.explosion=exploded_module.ExplodedView(Rhino.RhinoDoc.ActiveDoc,self.view)
            separation=data.get('FingerDistance',0)
            if math.isfinite(separation): self.explosion.update(max(0,min(1,separation)),self.explosion_factor)
            self.exploding=True
            return
        if self.exploding:
            if (data.get('HandValid') is False or data.get('SmoothReturn')) and self.explosion:
                self.return_started=time.monotonic()
                self.advance_return();return
            self.exploding=False
            # Release always returns every part and the pre-explosion camera.
            if self.explosion:
                self.explosion.restore();self.explosion=None
            self.basis.Dispose();self.basis=Rhino.DocObjects.ViewportInfo(self.view.ActiveViewport)
            self.basis.UnlockCamera()
            self.target=self.view.ActiveViewport.CameraTarget
            self.distance=self.basis.CameraLocation.DistanceTo(self.target)
            values=[0,0,0]
        grip=mode=='object' and data.get('Grip',False)
        if grip:
            hx,hy=data.get('HandX',0),data.get('HandY',0)
            if not all(math.isfinite(a) for a in (hx,hy)): return
            hand_size=data.get('HandSize',0)
            if not math.isfinite(hand_size) or hand_size<0:return
            if not self.grabbing:
                self.hand_size_origin=hand_size
                self.smooth_zoom=1.
                doc=Rhino.RhinoDoc.ActiveDoc
                objects=list(doc.Objects.GetSelectedObjects(False,False))
                if not objects:
                    objects=[o for o in doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject) if not o.IsHidden and not o.IsLocked]
                box=Rhino.Geometry.BoundingBox.Unset
                for obj in objects:
                    if isinstance(obj.Geometry,(Rhino.Geometry.Brep,Rhino.Geometry.Mesh,Rhino.Geometry.Extrusion,Rhino.Geometry.InstanceReferenceGeometry)):
                        box.Union(obj.Geometry.GetBoundingBox(True))
                if box.IsValid:self.target=box.Center
                self.basis.Dispose()
                self.basis=Rhino.DocObjects.ViewportInfo(self.view.ActiveViewport)
                self.basis.UnlockCamera()
                self.hand_origin=(hx,hy)
                self.smooth_hand=(hx,hy)
                self.grab_basis=Rhino.DocObjects.ViewportInfo(self.basis)
                self.grabbing=True
            sx,sy=self.smooth_hand
            self.smooth_hand=(sx+min(.85,.35*self.sensitivity)*(hx-sx),sy+min(.85,.35*self.sensitivity)*(hy-sy))
            yaw=-(self.smooth_hand[0]-self.hand_origin[0])*math.pi*2*self.strength
            pitch=max(-1.2,min(1.2,(self.smooth_hand[1]-self.hand_origin[1])*math.pi*2*self.strength))
            rotation=Rhino.Geometry.Transform.Rotation(yaw,self.grab_basis.CameraUp,self.target)*Rhino.Geometry.Transform.Rotation(pitch,self.grab_basis.CameraX,self.target)
            # A larger palm means a closer hand: dolly inward, without changing FOV.
            ratio=self.hand_size_origin/hand_size if hand_size>1e-6 and self.hand_size_origin>1e-6 else 1.
            if abs(ratio-1)<.03:ratio=1.
            desired=max(.35,min(2.5,1+(ratio-1)*self.strength))
            self.smooth_zoom+=min(.8,.22*self.sensitivity)*(desired-self.smooth_zoom)
            location=rotation*self.grab_basis.CameraLocation
            self.basis.SetCameraLocation(self.target+(location-self.target)*self.smooth_zoom)
            self.basis.SetCameraDirection(rotation*self.grab_basis.CameraDirection)
            self.basis.SetCameraUp(rotation*self.grab_basis.CameraUp)
            self.view.ActiveViewport.SetViewProjection(self.basis,False)
            self.view.Redraw()
            return
        if self.grabbing:
            self.grabbing=False
            self.grab_basis.Dispose()
            self.distance=self.basis.CameraLocation.DistanceTo(self.target)
            values=[0,0,0]
        if data.get('HeadValid') is False: return
        projection=Rhino.DocObjects.ViewportInfo(self.basis)
        try:
            projection.UnlockFrustumSymmetry()
            ok,left,right,bottom,top,near,far=self.basis.GetFrustum()
            if not ok: raise RuntimeError('無法讀取視錐')
            x,y=[max(-.3,min(.3,v))*self.distance for v in values[:2]]
            z=max(-.25,min(.5,values[2]))*self.distance
            projection.SetCameraLocation(self.basis.CameraLocation+self.basis.CameraX*x+self.basis.CameraY*y+self.basis.CameraZ*z)
            # Keep angular field of view fixed while dollying. A closer eye
            # makes objects larger through distance, rather than lens zoom.
            viewing_distance=self.distance+z
            projection.SetFrustum(left-x*near/viewing_distance,right-x*near/viewing_distance,
                bottom-y*near/viewing_distance,top-y*near/viewing_distance,near,far)
            if not self.view.ActiveViewport.SetViewProjection(projection,False): raise RuntimeError('投影更新失敗')
            self.view.Redraw()
        finally: projection.Dispose()
