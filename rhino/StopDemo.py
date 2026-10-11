#! python 3
import Rhino
import scriptcontext

state = scriptcontext.sticky.pop("NakedEye3D.Demo", None)
if state:
    state[0].Stop()
    state[1].close()
Rhino.RhinoApp.RunScript("_NakedEye3DStop", False)
print("NakedEye3D demo stopped; original camera restored.")
