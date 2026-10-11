"""Package just the Windows Rhino app, models and public assets; no runtime data."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[1]
output=root/'dist'/'NakedEye3D-Windows-Rhino8.zip'
output.parent.mkdir(exist_ok=True)
files=['rhino/TrackingPanel.py','rhino/ViewportTracking.py','rhino/ExplodedView.py',
       'tools/webcam_tracker.py','tools/hand_gestures.py',
       'models/face_landmarker.task','models/hand_landmarker.task','assets/face-cover.gif',
       'windows/Install.cmd','windows/Install.ps1','windows/requirements.txt',
       'windows/OpenPanel.py','windows/CheckSetup.cmd','windows/CheckSetup.py','windows/README.md','windows/README.en.md']
with ZipFile(output,'w',ZIP_DEFLATED) as z:
    for name in files:z.write(root/name,'NakedEye3D/'+name)
    binary=root/'dist/windows-build/NakedEye3D.rhp'
    if not binary.exists():raise FileNotFoundError('Build Release rhp first')
    z.write(binary,'NakedEye3D/rhino/bin/Debug/net7.0/NakedEye3D.rhp')
with ZipFile(output) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)+1
    for name in z.namelist():
        if name.endswith('.py'):compile(z.read(name),name,'exec')
print(output)
print(f'{output.stat().st_size/1024/1024:.1f} MB; ZIP integrity and Python compilation passed')
