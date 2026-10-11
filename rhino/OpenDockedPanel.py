#! python 3
"""Open the registered Rhino panel without opening or modifying a model."""
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
import Rhino
import System
script_path=unquote(urlparse(__file__).path) if __file__.startswith('file:') else __file__
if os.name=='nt' and script_path.startswith('/') and script_path[2:3]==':':script_path=script_path[1:]
root=Path(script_path).resolve().parents[1]
os.environ['VIEWMOTION_ROOT']=str(root)
plugin_id=System.Guid('49e67db1-636e-4d38-aeae-52724c1b8ad5')
if Rhino.PlugIns.PlugIn.Find(plugin_id) is None:
    raise RuntimeError('請先安裝 rhino/DockedPanel/bin/Debug/net7.0/RhinoViewMotion.DockPanel.rhp')
panel_id=System.Guid('eabb6fb8-4314-4429-8810-bb8dc24b8923')
# Respect the container chosen by the user, including a docked sidebar on Mac.
# FloatPanel would move the panel back into a separate floating window.
Rhino.UI.Panels.OpenPanel(panel_id,True)
