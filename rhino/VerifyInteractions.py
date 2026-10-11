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
    packet(Grip=True,HandX=0,HandY=0)
    packet(Grip=True,HandX=.12,HandY=.04)
    assert tracker.grabbing
    assert view.ActiveViewport.CameraLocation.DistanceTo(before.CameraLocation)>1e-5
    packet(Grip=False)
    assert not tracker.grabbing
    before.Dispose()
    print('PASS: inward fingers restore exactly; release restores geometry/camera; grab rotates and releases')
finally:
    if tracker:tracker.stop(False)
    for i in ids:doc.Objects.Delete(i,True)
    doc.Objects.UnselectAll()
    for i in selected:doc.Objects.Select(i)
    view.ActiveViewport.SetViewProjection(saved,False);saved.Dispose();view.Redraw()
exec(compile(open(ROOT+'/rhino/TrackingPanel.py').read(),'TrackingPanel.py','exec'))
