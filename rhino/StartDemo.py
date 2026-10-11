#! python 3
"""Run in Rhino 8 ScriptEditor: load plugin and start a simulated demo."""
import os
import json
import math
import socket
import time
import Rhino
import Eto.Forms as forms
import scriptcontext

ROOT = "/Users/zionw/Desktop/Codex/裸視3D"
KEY = "NakedEye3D.Demo"
doc = globals().get("__rhino_doc__", Rhino.RhinoDoc.ActiveDoc)
old = scriptcontext.sticky.pop(KEY, None)
if old:
    old[0].Stop()
    old[1].close()
Rhino.RhinoApp.RunScript("_NakedEye3DStop", False)
result, plugin_id = Rhino.PlugIns.PlugIn.LoadPlugIn(os.path.join(ROOT, "rhino/bin/Debug/net7.0/NakedEye3D.rhp"))
if str(result) != "Success":
    raise RuntimeError("Plugin load failed: " + str(result))
view = next((v for v in doc.Views if v.ActiveViewport.IsPerspectiveProjection), None)
if view is None:
    raise RuntimeError("Open a perspective viewport first")
doc.Views.ActiveView = view

# Populate only an empty document so the parallax has visible depth cues.
if doc.Objects.Count == 0:
    import System.Drawing as drawing
    layer = Rhino.DocObjects.Layer()
    layer.Name = "NakedEye3D_Demo"
    layer.Color = drawing.Color.FromArgb(80, 160, 195)
    index = doc.Layers.Add(layer)
    attributes = Rhino.DocObjects.ObjectAttributes()
    attributes.LayerIndex = index
    for x, y, z, radius in [(-35, 0, 15, 15), (0, 30, 25, 25), (40, 60, 20, 20)]:
        doc.Objects.AddSphere(Rhino.Geometry.Sphere(Rhino.Geometry.Point3d(x, y, z), radius), attributes)
    view.ActiveViewport.ZoomExtents()
    view.ActiveViewport.DisplayMode = Rhino.Display.DisplayModeDescription.FindByName("Shaded")
    doc.Views.Redraw()
if not Rhino.RhinoApp.RunScript("_NakedEye3DStart", False):
    raise RuntimeError("NakedEye3DStart failed")

sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
started = time.monotonic()
timer = forms.UITimer()
timer.Interval = 1.0 / 30.0

def tick(s, e):
    t = time.monotonic() - started
    data = dict(X=.1 * math.sin(t), Y=.05 * math.cos(t), Z=.04 * math.sin(t / 2),
                Grip=5 <= t % 12 < 9, HandX=.2 * math.sin(t), HandY=.1 * math.cos(t))
    sender.sendto(json.dumps(data).encode(), ("127.0.0.1", 39539))

timer.Elapsed += tick
scriptcontext.sticky[KEY] = (timer, sender, tick)
timer.Start()
print("NakedEye3D demo running: simulated head motion and grip rotation. Run StopDemo.py to stop.")
