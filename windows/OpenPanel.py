#! python 3
"""Run in Rhino 8 ScriptEditor once; registers ViewMotionPanel alias."""
import os
from pathlib import Path
import rhinoscriptsyntax as rs
from urllib.parse import urlparse, unquote
script_path=unquote(urlparse(__file__).path) if __file__.startswith('file:') else __file__
if os.name=='nt' and script_path.startswith('/') and len(script_path)>2 and script_path[2]==':':script_path=script_path[1:]
root=Path(script_path).resolve().parents[1]
os.environ['VIEWMOTION_ROOT']=str(root)
entry=root/'windows'/'OpenPanel.py'
rs.AddAlias('ViewMotionPanel','_-ScriptEditor _Run "'+str(entry)+'"')
panel=root/'rhino'/'TrackingPanel.py'
exec(compile(panel.read_text(encoding='utf-8'),str(panel),'exec'))
