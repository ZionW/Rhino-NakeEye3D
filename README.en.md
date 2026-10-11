# Rhino ViewMotion

[中文](README.md) · [English](README.en.md)

Webcam head and gesture tracking for interactive, single-viewer motion parallax in Rhino. It tracks viewer position to adjust the camera; it does not track gaze direction or deliver separate stereo images to each eye.

**Incomplete experimental beta with known issues. Test on copies of your models.** The Laughing Man image is used only as a tribute to Ghost in the Shell and for testing, and will be replaced. Rights remain with the original rights holders.

## Features

- Space mode: sideways, vertical and forward/backward head movement controls the view.
- Object mode: thumb/index/middle grasp orbits the camera; palm depth movement brings the camera closer or farther away. Head control pauses during grasping.
- Exploded view: choose two index fingers or single-hand fist/open-palm control. Adjustable ratio, smooth closing and restoration after lost hand tracking. Requires at least two separate components. Automatic framing respects viewport aspect with a small margin.
- Native Rhino panel, one Start/Pause button, Chinese/English/Japanese UI, Help, view strength and sensitivity sliders.
- Local webcam preview, animated face cover, hand skeleton and grasp indicator.
- Uses the current document and perspective viewport. Start captures the camera baseline; Stop restores it. No automatic demo document loading.
- Full screen invokes Rhino `Fullscreen`; Esc returns. Mac Rhino 8 does not support that command.

## Installation

If an earlier branded Yak is installed, remove it in PackageManager before installing this release. The plug-in ID is retained; avoid simultaneous installations. The Mac webcam launcher currently targets Apple Silicon.

1. Download the matching Rhino 8.35+ or Rhino 9 Yak from [Releases](https://github.com/ZionW/Rhino-ViewMotion/releases).
2. Run `PackageManager`, choose Install from file, and restart Rhino after installation.
3. Before webcam use, run `tools/setup_yak_runtime.py` in the installed package with Python 3.11. Windows: `py -3.11 tools/setup_yak_runtime.py`; Mac: `python3.11 tools/setup_yak_runtime.py`. Internet access is required for dependencies.
4. Run **`ViewMotionPanel`**, activate a perspective viewport and start tracking. Allow ViewMotion Webcam when macOS requests camera access.
5. Right-click a sidebar panel tab and enable **Rhino ViewMotion** in the panel list to use that container.

Rhino 9 macOS docking, webcam preview and head tracking have been tested. Windows hardware testing is pending. Full gestures, multi-document switching and cross-hardware stability remain under validation. Webcam depth is an estimate; physical screen calibration is incomplete.

## Test screenshots

These Rhino 9 screenshots were captured before renaming and still show the previous branding.

![Space mode](docs/images/rhino9-space-mode.png)

![Object mode / exploded-view test](docs/images/rhino9-exploded-view.png)

## Development

TrackingPanel.py manages controls; ViewportTracking.py controls the camera; ExplodedView.py manages part positions; webcam_tracker.py processes local tracking. Rhino 8 targets net7.0; the installed Rhino 9 Beta targets net10.0, built separately.

```sh
python3 -m unittest discover -s tools -p 'test_hand_gestures.py'
python3 tools/build_yak.py
```

Building requires .NET SDK, Rhino 8/9 and MediaPipe models. `--skip-build` packages existing Release binaries. Both Yak packages undergo integrity and Python syntax checks. [Test guide](TEST_GUIDE.md)

## Data and assets

Tracking services bind only to localhost. One preview image is temporarily stored in runtime/preview.jpg, continuously overwritten and removed on normal shutdown. No recording or uploading. The GIF is not a guarantee of anonymization. Runtime, environments, model caches and archived packages are excluded from version control. MediaPipe models and Laughing Man assets remain subject to their respective owners' rights.
