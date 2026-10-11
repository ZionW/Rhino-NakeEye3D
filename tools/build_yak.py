"""Build and verify local Rhino ViewMotion Yak packages, without publishing."""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.3.0-beta.1'
ASSEMBLY='RhinoViewMotion.DockPanel'
FILES=['rhino/TrackingPanel.py','rhino/ViewportTracking.py','rhino/ExplodedView.py',
       'rhino/OpenDockedPanel.py','rhino/DockedPanel/PanelIcon.svg',
       'tools/webcam_tracker.py','tools/hand_gestures.py','tools/setup_yak_runtime.py',
       'models/face_landmarker.task','models/hand_landmarker.task',
       'assets/face-cover.gif','windows/requirements.txt','README.md','README.en.md',
       'docs/images/rhino9-space-mode.png','docs/images/rhino9-exploded-view.png']

def verify(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        names=archive.namelist()
        assert ASSEMBLY+'.rhp' in names and 'manifest.yml' in names
        assert not any('runtime/' in n or '.venv/' in n for n in names)
        for name in names:
            if name.endswith('.py'):compile(archive.read(name),name,'exec')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-build',action='store_true')
    parser.add_argument('--configfile')
    parser.add_argument('--yak',default='/Applications/Rhino 8.app/Contents/Resources/bin/yak')
    args=parser.parse_args()
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    for project,framework,tag in [('RhinoViewMotion.Panel.csproj','net7.0','rh8_35-any'),('Rhino9.csproj','net10.0','rh9_0-any')]:
        if not args.skip_build:
            command=['dotnet','build',str(ROOT/'rhino/DockedPanel'/project),'-c','Release','-p:UseSharedCompilation=false']
            if args.configfile:command+=['--configfile',args.configfile]
            subprocess.run(command,check=True)
        with tempfile.TemporaryDirectory(prefix='viewmotion-yak-') as folder:
            stage=Path(folder)
            for name in FILES:
                target=stage/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/name,target)
            shutil.copytree(ROOT/'tools/ViewMotion Webcam.app',stage/'tools/ViewMotion Webcam.app')
            for ext in ['rhp','deps.json','runtimeconfig.json']:
                filename=ASSEMBLY+'.'+ext
                shutil.copy2(ROOT/'rhino/DockedPanel/bin/Release'/framework/filename,stage/filename)
            (stage/'manifest.yml').write_text(f'''name: rhino-viewmotion
version: {VERSION}
authors:
  - ZionW
description: Experimental beta. Incomplete webcam head and gesture tracking; Python 3.11 setup required. / 功能尚不完善的頭部與手勢追蹤測試版。
url: https://github.com/ZionW/Rhino-ViewMotion
keywords:
  - guid:49e67db1-636e-4d38-aeae-52724c1b8ad5
  - webcam
  - tracking
''')
            subprocess.run([args.yak,'build','--platform','any'],cwd=stage,check=True)
            package=next(stage.glob('*.yak'))
            target=output/f'rhino-viewmotion-{VERSION}-{tag}.yak'
            shutil.copy2(package,target);verify(target)
            print(target)

if __name__=='__main__':main()
