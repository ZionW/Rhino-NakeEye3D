"""Scale-independent three-finger clutch; no camera or inference dependencies."""
import math

def distance(a, b):
    return math.sqrt(sum((getattr(a,k)-getattr(b,k))**2 for k in ('x','y','z')))

def flexion(points, base, joint, tip):
    a,b,c=(points[i] for i in (base,joint,tip))
    u=[getattr(a,k)-getattr(b,k) for k in ('x','y','z')]
    v=[getattr(c,k)-getattr(b,k) for k in ('x','y','z')]
    length=math.sqrt(sum(x*x for x in u)*sum(x*x for x in v))
    if length<1e-9: return 1.
    return 1-math.acos(max(-1.,min(1.,sum(x*y for x,y in zip(u,v))/length)))/math.pi

def index_only(points):
    return flexion(points,5,6,8)<.18 and flexion(points,1,2,4)>.12 and all(flexion(points,*f)>.22 for f in [(9,10,12),(13,14,16),(17,18,20)])

def three_finger_grasp(points, active=False):
    """Bring thumb, index and middle tips together, like holding a small knob.

    Ring/pinky can relax naturally. Both controlling fingers must be bent but
    remain outside the palm; a closed fist and an extended index cannot clutch.
    """
    palm=distance(points[5],points[17])
    if palm<1e-6 or index_only(points): return False
    curls=[flexion(points,*f) for f in [(5,6,8),(9,10,12),(13,14,16),(17,18,20)]]
    if all(c>.55 for c in curls): return False
    if not all((.06 if active else .09)<c<.86 for c in curls[:2]): return False
    limit=1.0 if active else .78
    if max(distance(points[a],points[b])/palm for a,b in [(4,8),(4,12),(8,12)])>limit: return False
    # Fist tips fold into the palm, whereas a tripod pinch stays distal to MCPs.
    return all(distance(points[0],points[i])>distance(points[0],points[base])*.80 for i,base in [(8,5),(12,9)])
