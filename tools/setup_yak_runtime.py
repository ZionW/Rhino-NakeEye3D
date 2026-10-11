"""Run with Python 3.11 after Yak install, before starting webcam tracking."""
from pathlib import Path
import sys, subprocess, venv
if sys.version_info[:2] != (3,11):raise SystemExit('Use Python 3.11 / 請使用 Python 3.11')
root=Path(__file__).resolve().parents[1]
venv.EnvBuilder(with_pip=True).create(root/'.venv')
python=root/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
subprocess.run([str(python),'-m','pip','install','-r',str(root/'windows/requirements.txt')],check=True)
print('Ready. In Rhino run NakeEye3DDockPanel / 就緒，請在 Rhino 執行 NakeEye3DDockPanel')
