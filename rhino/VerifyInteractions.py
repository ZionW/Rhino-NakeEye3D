"""Rhino MCP regression: temporary assembly, exact geometry/view restoration."""
import sys,importlib,json
import Rhino,scriptcontext
ROOT='/Users/zionw/Desktop/Codex/裸視3D'
if ROOT+'/rhino' not in sys.path:sys.path.insert(0,ROOT+'/rhino')
panel=scriptcontext.sticky.get('NakedEye3D.Panel')
if panel:panel.Close()
import ExplodedView,ViewportTracking
importlib.reload(ExplodedView);importlib.reload(ViewportTracking)
doc=Rhino.RhinoDoc.ActiveDoc;view=doc.Views.ActiveView
saved=Rhino.DocObjects.ViewportInfo(view.ActiveViewport)
selected=[o.Id for o in doc.Objects.GetSelectedObjects(False,False)]
ids=[];tracker=None
class Packets:
    def __init__(self,data):self.data=data
    def recv(self,size):
        if not self.data:raise BlockingIOError()
        return json.dumps(self.data.pop(0)).encode()
    def close(self):pass
try:
    doc.Objects.UnselectAll()
    for x in [-3,3]:
        ident=doc.Objects.AddBrep(Rhino.Geometry.Sphere(Rhino.Geometry.Point3d(x,0,0),1).ToBrep())
        ids.append(ident);doc.Objects.Select(ident)
    original=[doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center for i in ids]
    exp=ExplodedView.ExplodedView(doc,view)
    for _ in range(12):exp.update(.6)
    assert doc.Objects.FindId(ids[0]).Geometry.GetBoundingBox(True).Center.DistanceTo(original[0])>1
    factor3=exp.factor
    for _ in range(12):exp.update(.6,5.)
    assert factor3<exp.factor<=5.
    exp.update(.6,1.)
    assert exp.factor==1.
    exp.update(.08)
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    assert view.ActiveViewport.CameraLocation.DistanceTo(saved.CameraLocation)<1e-8
    exp.restore()
    tracker=ViewportTracking.ViewportTracking();tracker.start(view);tracker.mode='object'
    tracker.socket.close()
    def packet(**kw):
        tracker.socket=Packets([dict(Mode='object',X=0,Y=0,Z=0,HeadValid=False,**kw)]);tracker.update()
    before=Rhino.DocObjects.ViewportInfo(view.ActiveViewport)
    for _ in range(12):packet(Explode=True,FingerDistance=.6)
    packet(Explode=False,Grip=False)
    assert tracker.explosion is None
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    assert view.ActiveViewport.CameraLocation.DistanceTo(before.CameraLocation)<1e-8
    for _ in range(8):packet(Explode=True,FingerDistance=.6)
    tracker.reset_explosion()
    packet(Explode=True,FingerDistance=.6)
    assert tracker.explosion is None
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    packet(Explode=False,Grip=False)
    for _ in range(12):packet(Explode=True,FingerDistance=.6,HandValid=True)
    opened=tracker.explosion.factor
    for _ in range(6):packet(Explode=True,FingerDistance=.3,HandValid=True,SmoothReturn=True)
    assert 1<tracker.explosion.factor<opened
    packet(Explode=False,Grip=False,HandValid=True,SmoothReturn=True)
    assert tracker.return_started is not None
    tracker.return_started-=1;tracker.update()
    packet(Explode=False,Grip=False)
    for _ in range(12):packet(Explode=True,FingerDistance=.6,HandValid=True)
    expanded=doc.Objects.FindId(ids[0]).Geometry.GetBoundingBox(True).Center.DistanceTo(original[0])
    packet(Explode=False,Grip=False,HandValid=False)
    assert tracker.return_started is not None
    assert doc.Objects.FindId(ids[0]).Geometry.GetBoundingBox(True).Center.DistanceTo(original[0])>expanded*.9
    tracker.return_started-=.35;tracker.update()
    halfway=doc.Objects.FindId(ids[0]).Geometry.GetBoundingBox(True).Center.DistanceTo(original[0])
    assert 0<halfway<expanded
    tracker.return_started-=1;tracker.update()
    assert tracker.explosion is None and tracker.return_started is None
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    packet(Explode=False,Grip=False)
    packet(Grip=True,HandX=0,HandY=0)
    orbit_distance=view.ActiveViewport.CameraLocation.DistanceTo(tracker.target)
    packet(Grip=True,HandX=.12,HandY=.04)
    assert abs(view.ActiveViewport.CameraLocation.DistanceTo(tracker.target)-orbit_distance)<1e-7
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    assert tracker.grabbing
    assert view.ActiveViewport.CameraLocation.DistanceTo(before.CameraLocation)>1e-5
    packet(Grip=False)
    packet(Grip=True,HandX=0,HandY=0,HandSize=1.)
    neutral=view.ActiveViewport.CameraLocation.DistanceTo(tracker.target)
    for _ in range(12):packet(Grip=True,HandX=0,HandY=0,HandSize=1.5)
    assert view.ActiveViewport.CameraLocation.DistanceTo(tracker.target)<neutral*.9
    for _ in range(18):packet(Grip=True,HandX=0,HandY=0,HandSize=.6)
    assert view.ActiveViewport.CameraLocation.DistanceTo(tracker.target)>neutral*1.2
    assert all(doc.Objects.FindId(i).Geometry.GetBoundingBox(True).Center.DistanceTo(p)<1e-8 for i,p in zip(ids,original))
    packet(Grip=False)
    assert not tracker.grabbing
    before.Dispose()
    print('PASS: inward fingers restore exactly; release restores geometry/camera; grab rotates and releases; hand loss returns gradually')
finally:
    if tracker:tracker.stop(False)
    for i in ids:doc.Objects.Delete(i,True)
    doc.Objects.UnselectAll()
    for i in selected:doc.Objects.Select(i)
    view.ActiveViewport.SetViewProjection(saved,False);saved.Dispose();view.Redraw()
import os
os.environ['NAKEDEYE3D_ROOT']=ROOT
exec(compile(open(ROOT+'/rhino/TrackingPanel.py').read(),'TrackingPanel.py','exec'))
