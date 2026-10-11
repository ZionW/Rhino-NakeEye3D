# Rhino NakeEye3D · 裸視3D

[中文](README.md) · [English](README.en.md)

**Experimental beta: incomplete, with known issues. Test on copies of your models.** The Laughing Man image is used only as a tribute to Ghost in the Shell and for feature testing, and will be replaced in a future version. Rights remain with the original rights holders.

## Rhino 9 test screenshots

Space mode and webcam panel:

![Space mode](docs/images/rhino9-space-mode.png)

Object mode / exploded-view test (framing remains under development):

![Exploded-view test](docs/images/rhino9-exploded-view.png)

Webcam head and hand tracking for view-dependent 3D on an ordinary monitor. This project contains only the Rhino plug-in. It provides single-viewer motion parallax, not binocular stereo. Webcam depth is an estimate; physical screen calibration is not complete.

## Rhino features

- **Space mode:** horizontal, vertical and forward/backward head movement controls the camera.
- **Object mode:** grasp with thumb, index and middle finger, then move the hand to orbit the camera. Head control pauses during the grasp.
- **Exploded view:** choose two index fingers or single-hand fist/open-palm control, with an adjustable explosion ratio. Lost hand tracking gradually restores parts. Bringing them together or releasing restores the original positions. Automatic camera framing keeps parts visible. At least two separate objects are required.
- Start/resume captures the current perspective camera as the baseline; stopping restores it.
- Chinese, English and Japanese UI; a separate instructions dialog; view strength and sensitivity sliders.
- 224×168 webcam preview, animated face cover, hand skeleton and grip indicator. Eye markers are disabled.
- Wave rotation is disabled. The floating panel belongs to Rhino and does not use system-wide always-on-top.
- Full screen invokes Rhino's `_Fullscreen` command; Esc returns. **Mac Rhino 8 currently does not support this command.** Windows behavior still needs hardware testing.

## Windows Rhino 8 setup

Requirements: Windows 10/11 x64, Rhino 8 and Python 3.11 x64. Installing Python dependencies requires internet access.

1. Download the [Windows test package](dist/NakedEye3D-Windows-Rhino8.zip) and extract it to a writable directory.
2. Run `windows\Install.cmd` to create an isolated Python environment and install dependencies.
3. Optionally run `windows\CheckSetup.cmd` to validate models and dependencies without opening the camera.
4. In Rhino run `_-ScriptEditor _Run` and select `windows\OpenPanel.py`.
5. Later, enter `NakedEye3DPanel`, activate a perspective viewport and click Start / resume.

The panel uses the currently open Rhino document. Opening it does not load test files or add sample objects. Tracking starts from the active perspective viewport and its current camera settings.

Registered Rhino panel preview: build `rhino/DockedPanel/RhinoNakeEye3D.Panel.csproj`, load the resulting `RhinoNakeEye3D.DockPanel.rhp` with Rhino's `TestLoadPlugin`, then run `rhino/OpenDockedPanel.py`. Windows uses Rhino's tabbed panel system; Mac uses a Rhino-managed floating panel. Rhino 9 macOS sidebar docking, webcam preview and head tracking have been tested. Windows hardware testing is pending. The new Release includes Yak packages.

The ZIP includes the compiled plug-in, tracking models and face-cover asset. A source checkout requires building the `.rhp` first. See [Windows setup details](windows/README.md) and [English setup details](windows/README.en.md).

## Development and verification

The macOS implementation has been tested with Rhino camera control, restoration, webcam tracking and simulated gestures. The Windows package passed build and packaging checks but has not been run on Windows hardware. Use a copy of your model for initial testing.

```sh
dotnet build rhino/NakedEye3D.csproj
python3 -m unittest discover -s tools -p 'test_hand_gestures.py'
```

`rhino/TrackingPanel.py` implements the Eto floating panel. `ViewportTracking.py` handles projection and orbiting; `ExplodedView.py` restores part geometry. `tools/webcam_tracker.py` performs tracking in a separate process. The Windows bootstrap registers the panel command and resolves the project directory.

On macOS, the webcam worker uses `tools/NakedEye3D Webcam.app`; rebuilding requires Python dependencies and a camera usage declaration. This macOS launcher is separate from the Windows package.

## Data and third-party assets

Tracking and preview services bind only to localhost, `127.0.0.1`. The preview overwrites one local runtime/preview.jpg image; it is not uploaded. The GIF is a visual cover, not a guarantee of anonymization. Runtime files, Python environments, caches and local logs are excluded from version control.

Models originate from Google MediaPipe. The face-cover GIF was supplied by the user. Third-party models, trademarks and assets remain subject to their respective owners' rights; this project does not grant a separate license to those assets.

## Yak preview (Rhino 8.35+ / Rhino 9)

Install the matching .yak from dist using PackageManager → Install from file, then restart Rhino. Before webcam use, run tools/setup_yak_runtime.py from the installed package with Python 3.11 (requires internet for dependencies). Windows: `py -3.11 tools/setup_yak_runtime.py`; Mac: `python3.11 tools/setup_yak_runtime.py`. Open with `NakeEye3DDockPanel`. Not published to the Yak server; Rhino 9 macOS panel, webcam preview and head tracking have been tested; full gesture and hardware stability validation remains pending.
