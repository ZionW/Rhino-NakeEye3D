"""Validate Windows webcam dependencies and model assets without opening camera."""
from pathlib import Path
import platform
import cv2
import mediapipe as mp
from PIL import Image
root=Path(__file__).resolve().parents[1]
print('Platform:',platform.platform())
print('OpenCV:',cv2.__version__,'MediaPipe:',mp.__version__)
base=mp.tasks.BaseOptions
vision=mp.tasks.vision
with vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=base(model_asset_path=str(root/'models/face_landmarker.task')))):
    print('Face model: OK')
with vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(base_options=base(model_asset_path=str(root/'models/hand_landmarker.task')))):
    print('Hand model: OK')
with Image.open(root/'assets/face-cover.gif') as im:
    print('Face cover:',im.size,'frames:',im.n_frames)
print('PASS: setup ready. Open the panel in Rhino to test webcam and Fullscreen.')
