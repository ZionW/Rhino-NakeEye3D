# Windows Rhino 8 test package

[中文](README.md) · [English](README.en.md)

Requires Windows 10/11 x64, Rhino 8 and Python 3.11 x64.

1. Extract the entire package to a writable directory. Do not run it inside the ZIP.
2. If needed, install Python 3.11 x64 from https://www.python.org/downloads/windows/ with the Python Launcher.
3. Run `Install.cmd`; it creates `.venv` and installs dependencies from PyPI.
4. Run `CheckSetup.cmd` to check the tracking models and dependencies.
5. In Rhino run `_-ScriptEditor _Run` and select `OpenPanel.py`. This registers `NakedEye3DPanel` for subsequent use.
6. Activate a perspective viewport and click Start / resume.

Space mode tracks head movement. Object mode uses a thumb/index/middle grasp to orbit the camera. Two extended index fingers control the exploded view; bringing them together or releasing restores the model. Full screen runs Rhino `_Fullscreen`; press Esc to return.

Windows Settings → Privacy & security → Camera must allow desktop applications to use the camera. Stop tracking in other applications before starting. If needed, stop and change the camera index. Logs are in `runtime\webcam.log`.

The Windows package passed build, syntax and ZIP checks on macOS; Windows hardware validation is pending. Test with a copy of your model.
