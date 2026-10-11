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

    def update(self,separation,max_factor=3.):
        if not self.parts: return False
        desired=1+(max(1.,min(5.,max_factor))-1)*max(0,min(1,(separation-.08)/.52))
        self.factor=1. if desired<=1.04 else self.factor+.22*(desired-self.factor)
        bounds=self.place_parts()
        vp=self.view.ActiveViewport
        camera=Rhino.DocObjects.ViewportInfo(vp)
        camera.UnlockCamera(); camera.UnlockFrustumSymmetry()
        ok,left,right,bottom,top,near,far=self.saved_camera.GetFrustum()
        # Fit every bounding-box corner using the original angular field of view.
        tan_y=(top-bottom)/(2*near)
        size=vp.Size
        aspect=float(size.Width)/max(1,size.Height)
        tan_x=tan_y*aspect
        # Center the frustum on the complete exploded assembly, including
        # uneven component distributions and resized/docked viewports.
        left,right=-tan_x*near,tan_x*near
        bottom,top=-tan_y*near,tan_y*near
        fit_center=bounds.Center
        required=near*2
        for p in bounds.GetCorners():
            offset=p-fit_center
            cx=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraX)
            cy=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraY)
            cz=Rhino.Geometry.Vector3d.Multiply(offset,camera.CameraZ)
            required=max(required,cz+abs(cx)/max(tan_x,.001)*1.02,cz+abs(cy)/max(tan_y,.001)*1.02)
        camera.SetCameraLocation(fit_center+camera.CameraZ*required)
        camera.SetFrustum(left,right,bottom,top,near,max(far,required+self.radius*6))
        vp.SetViewProjection(camera,True)
        camera.Dispose();self.view.Redraw()
        return True

    def place_parts(self):
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
        return bounds

    def return_step(self,progress):
        if not self.parts:return
        if not hasattr(self,'return_factor'):
            self.return_factor=self.factor
            self.return_camera=Rhino.DocObjects.ViewportInfo(self.view.ActiveViewport)
        t=max(0.,min(1.,progress))
        eased=t*t*(3-2*t)
        self.factor=1+(self.return_factor-1)*(1-eased)
        self.place_parts()
        camera=Rhino.DocObjects.ViewportInfo(self.saved_camera)
        camera.UnlockCamera()
        camera.SetCameraLocation(self.return_camera.CameraLocation+(self.saved_camera.CameraLocation-self.return_camera.CameraLocation)*eased)
        self.view.ActiveViewport.SetViewProjection(camera,False)
        camera.Dispose();self.view.Redraw()

    def restore(self):
        if hasattr(self,'return_camera'):
            self.return_camera.Dispose();del self.return_camera
        for identifier,original,_ in self.parts:
            if self.doc.Objects.FindId(identifier): self.doc.Objects.Replace(identifier,original)
            original.Dispose()
        self.parts=[]
        if hasattr(self,'saved_camera'):
            self.view.ActiveViewport.SetViewProjection(self.saved_camera,False)
            self.saved_camera.Dispose()
            del self.saved_camera
            self.view.Redraw()
