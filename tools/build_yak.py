"""Build local Rhino 8/9 Yak distributions without publishing."""
from pathlib import Path
import shutil, subprocess, zipfile, sys
root=Path(__file__).resolve().parents[1]
stage=root/'dist/yak-build'
if stage.exists():shutil.rmtree(stage)
stage.mkdir(parents=True)
binary=root/'rhino/DockedPanel/bin/Release/net7.0'
if '--skip-build' not in sys.argv:subprocess.run(['dotnet','build',str(root/'rhino/DockedPanel/RhinoNakeEye3D.Panel.csproj'),'-c','Release','-p:UseSharedCompilation=false'],check=True)
for name in ['RhinoNakeEye3D.DockPanel.rhp','RhinoNakeEye3D.DockPanel.deps.json','RhinoNakeEye3D.DockPanel.runtimeconfig.json']:shutil.copy2(binary/name,stage/name)
files=['rhino/TrackingPanel.py','rhino/ViewportTracking.py','rhino/ExplodedView.py','rhino/OpenDockedPanel.py','rhino/DockedPanel/PanelIcon.svg','tools/webcam_tracker.py','tools/hand_gestures.py','models/face_landmarker.task','models/hand_landmarker.task','assets/face-cover.gif','windows/requirements.txt','tools/setup_yak_runtime.py','README.md','README.en.md','docs/images/rhino9-space-mode.png','docs/images/rhino9-exploded-view.png']
for name in files:
    target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
shutil.copytree(root/'tools/NakedEye3D Webcam.app',stage/'tools/NakedEye3D Webcam.app')
(stage/'manifest.yml').write_text('''name: rhino-nakeeye3d
version: 0.2.0-beta.2
authors:
  - ZionW
description: Webcam head tracking, gesture orbit and exploded views. Rhino 8 and 9 preview. Run tools/setup_yak_runtime.py with Python 3.11 before webcam use. / 裸視3D頭部與手勢追蹤，首次使用須安裝追蹤環境。
url: https://github.com/ZionW/Rhino-NakeEye3D
keywords:
  - guid:49e67db1-636e-4d38-aeae-52724c1b8ad5
  - webcam
  - tracking
''')
yak='/Applications/Rhino 8.app/Contents/Resources/bin/yak'
subprocess.run([yak,'build','--platform','any'],cwd=stage,check=True)
package=next(stage.glob('*.yak'))
for tag in ['rh8_35-any']:
    dest=root/'dist'/('rhino-nakeeye3d-0.2.0-beta.2-'+tag+'.yak');shutil.copy2(package,dest)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert not any('/runtime/' in n or '/.venv/' in n for n in z.namelist())
        for name in z.namelist():
            if name.endswith('.py'):compile(z.read(name),name,'exec')
    print(dest)

# Rhino 9 WIP uses .NET 10; build its own binary before packaging.
if '--skip-build' not in sys.argv:subprocess.run(['dotnet','build',str(root/'rhino/DockedPanel/Rhino9.csproj'),'-c','Release','-p:UseSharedCompilation=false'],check=True)
for ext in ['rhp','deps.json','runtimeconfig.json']:
    shutil.copy2(root/'rhino/DockedPanel/bin/Release/net10.0'/('RhinoNakeEye3D.DockPanel.'+ext),stage/('RhinoNakeEye3D.DockPanel.'+ext))
for old in stage.glob('*.yak'):old.unlink()
subprocess.run([yak,'build','--platform','any'],cwd=stage,check=True)
shutil.copy2(next(stage.glob('*.yak')),root/'dist/rhino-nakeeye3d-0.2.0-beta.2-rh9_0-any.yak')
