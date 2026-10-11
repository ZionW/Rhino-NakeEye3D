"""Rhino-compatible fixed-FOV head parallax, in imported scene units."""
import math

def updateCamera():
    b=parent();c=b.op('observer');s=b.fetch('state',{})
    if not b.par.Tracking or not s.get('base'):return
    x,y,z,rx,ry=s['base'];a=math.radians(ry);p=math.radians(rx)
    # The foreground vehicle is the viewing target, not the distant mountain.
    distance=math.sqrt(x*x+(y-1.2)**2+(z+1)**2)
    gain=b.par.Parallaxgain.eval()
    dx=max(-.3,min(.3,b.par.Headx.eval()*gain))*distance
    dy=max(-.3,min(.3,b.par.Heady.eval()*gain))*distance
    dz=max(-.25,min(.5,b.par.Headz.eval()))*distance
    right=(math.cos(a),0,-math.sin(a))
    up=(math.sin(a)*math.sin(p),math.cos(p),math.cos(a)*math.sin(p))
    back=(math.sin(a)*math.cos(p),-math.sin(p),math.cos(a)*math.cos(p))
    for name,origin,i in [('tx',x,0),('ty',y,1),('tz',z,2)]:
        setattr(c.par,name,origin+right[i]*dx+up[i]*dy+back[i]*dz)
    c.par.rx=rx;c.par.ry=ry
    # Match Rhino: fixed angular FOV with an off-axis shift, without dolly zoom.
    sx=1/math.tan(math.radians(c.par.fov.eval()/2));sy=sx*1280/720
    d=distance+dz;n=.05;f=5000
    matrix=b.op('eye_projection');matrix.clear()
    for row in [[sx,0,-dx/d*sx,0],[0,sy,-dy/d*sy,0],[0,0,-f/(f-n),-f*n/(f-n)],[0,0,-1,0]]:matrix.appendRow(row)
    c.par.projection='custommatrix';c.par.projmatrixop=matrix

def onFrameStart(frame):
    if parent().op('tracker_runtime').module.tick():updateCamera()

def onExit():parent().op('tracker_runtime').module.stop()
