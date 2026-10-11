import json
import socket
import time
from rhino_mcp import Client

def run(client, script):
    result = client.call('run_python', {'script': script})
    print(json.dumps(result, ensure_ascii=False))
    if result.get('isError'):
        raise RuntimeError('Rhino Python failed')

with Client() as client:
    run(client, '''import Rhino
import scriptcontext
path = "/Users/zionw/Desktop/Codex/裸視3D/rhino/bin/Debug/net7.0/NakedEye3D.rhp"
print("LOAD", Rhino.PlugIns.PlugIn.LoadPlugIn(path))
doc = __rhino_doc__
view = next(v for v in doc.Views if v.ActiveViewport.IsPerspectiveProjection)
doc.Views.ActiveView = view
v = view.ActiveViewport
scriptcontext.sticky["nakedeye_test_before"] = (v.CameraLocation, v.CameraTarget, v.GetFrustum())
print("START", Rhino.RhinoApp.RunScript("_NakedEye3DStart", False))
''')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for i in range(20):
                sock.sendto(json.dumps(dict(X=.1, Y=.05, Z=.02, Grip=False, HandX=0, HandY=0)).encode(), ('127.0.0.1',39539))
                time.sleep(.05)
        run(client, '''import Rhino
import scriptcontext
v = __rhino_doc__.Views.ActiveView.ActiveViewport
before = scriptcontext.sticky["nakedeye_test_before"]
assert v.CameraLocation.DistanceTo(before[0]) > 0.01, "Head motion did not move camera"
print("MOVED_CAMERA", v.CameraLocation)
print("STOP", Rhino.RhinoApp.RunScript("_NakedEye3DStop", False))
print("RESTORED_CAMERA", v.CameraLocation)
assert v.CameraLocation.DistanceTo(before[0]) < 1e-7, "Camera restore mismatch"
assert v.CameraTarget.DistanceTo(before[1]) < 1e-7, "Target restore mismatch"
assert v.GetFrustum() == before[2], "Frustum restore mismatch"
del scriptcontext.sticky["nakedeye_test_before"]
print("PASS: head motion and camera/target/frustum restoration")
''')
    finally:
        print(json.dumps(client.call('run_command', {'command':'_NakedEye3DStop'}), ensure_ascii=False))
