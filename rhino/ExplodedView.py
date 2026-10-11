import math
import Rhino

class ExplodedView:
    """Scale component positions around assembly center without scaling geometry."""
    def __init__(self,doc,view):
        self.doc=doc; self.view=view; self.parts=[]; self.factor=1.
        candidates=list(doc.Objects.GetSelectedObjects(False,False))
        if not candidates: candidates=list(doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject))
        for obj in candidates:
            if obj.IsHidden or obj.IsLocked: continue
            if not isinstance(obj.Geometry,(Rhino.Geometry.Brep,Rhino.Geometry.Mesh,Rhino.Geometry.Extrusion,Rhino.Geometry.InstanceReferenceGeometry)): continue
            box=obj.Geometry.GetBoundingBox(True)
            if box.IsValid: self.parts.append((obj.Id,obj.Geometry.Duplicate(),box.Center))
        if len(self.parts)<2:
            self.restore()
            return
        box=self.parts[0][1].GetBoundingBox(True)
        for _,geometry,_ in self.parts[1:]: box.Union(geometry.GetBoundingBox(True))
        self.center=box.Center
        self.radius=max(box.Diagonal.Length*.5,1e-3)
        self.saved_camera=Rhino.DocObjects.ViewportInfo(view.ActiveViewport)

    def update(self,separation):
        if not self.parts: return False
        desired=1+2*max(0,min(1,(separation-.08)/.52))
        self.factor=1. if desired<=1.04 else self.factor+.22*(desired-self.factor)
        bounds=Rhino.Geometry.BoundingBox.Unset
        for index,(identifier,original,center) in enumerate(self.parts):
            offset=center-self.center
            if offset.Length<self.radius*.01:
                angle=2*math.pi*index/len(self.parts)
                offset=Rhino.Geometry.Vector3d(math.cos(angle),math.sin(angle),0)*self.radius*.35
            delta=offset*(self.factor-1)
            geometry=original.Duplicate()
            geometry.Transform(Rhino.Geometry.Transform.Translation(delta))
            if self.doc.Objects.FindId(identifier): self.doc.Objects.Replace(identifier,geometry)
            bounds.Union(geometry.GetBoundingBox(True))
            geometry.Dispose()
        vp=self.view.ActiveViewport
        if self.factor==1.:
            vp.SetViewProjection(self.saved_camera,False)
            self.view.Redraw()
            return True
        camera=Rhino.DocObjects.ViewportInfo(vp)
        camera.UnlockCamera(); camera.UnlockFrustumSymmetry()
        ok,left,right,bottom,top,near,far=self.saved_camera.GetFrustum()
        # Fit every bounding-box corner using the original angular field of view.
        tan_x=min(abs(left),abs(right))/near
        tan_y=min(abs(top),abs(bottom))/near
        required=near*2
        for p in bounds.GetCorners():
            offset=p-self.center
            cx=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraX)
            cy=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraY)
            cz=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraZ)
            required=max(required,cz+abs(cx)/max(tan_x,.001)*1.15,cz+abs(cy)/max(tan_y,.001)*1.15)
        camera.SetCameraLocation(self.center+camera.CameraZ*required)
        camera.SetFrustum(left,right,bottom,top,near,max(far,required+self.radius*6))
        vp.SetViewProjection(camera,True)
        camera.Dispose();self.view.Redraw()
        return True

    def restore(self):
        for identifier,original,_ in self.parts:
            if self.doc.Objects.FindId(identifier): self.doc.Objects.Replace(identifier,original)
            original.Dispose()
        self.parts=[]
        if hasattr(self,'saved_camera'):
            self.view.ActiveViewport.SetViewProjection(self.saved_camera,False)
            self.saved_camera.Dispose()
            del self.saved_camera
            self.view.Redraw()
