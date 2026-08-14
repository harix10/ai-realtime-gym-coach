import os
import time
import cv2
import av
import numpy as np
import mediapipe as mp
import threading

from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from detectors.pushup import PushUpDetector
from detectors.squat import SquatDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector

from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        model_path = os.path.join(
            os.getcwd(),
            "ml_models",
            "pose_landmarker_full.task"
        )

        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False,
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
        }

    # ---------------------------
    # Thread-safe state methods
    # ---------------------------
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise_type(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise_type(self):
        with self._lock:
            return self._exercise_type

    # ---------------------------
    # Drawing helpers
    # ---------------------------
    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 255, 0),
                    4,
                )

        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    5,
                    (255, 0, 0),
                    -1,
                )

    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        h, _ = img.shape[:2]

        if ex_type == "Squats":
            text = f"DEPTH: {metrics.get('depth_status', 'N/A')}"

        elif ex_type == "Push-ups":
            text = (
                f"BODY: {metrics.get('body_alignment', 'N/A')} | "
                f"HIP: {metrics.get('hip_status', 'N/A')}"
            )

        elif ex_type == "Biceps Curls (Dumbbell)":
            text = f"SWING: {metrics.get('swing_status', 'N/A')}"

        elif ex_type == "Shoulder Press":
            text = (
                f"EXT: {metrics.get('extension_status', 'N/A')} | "
                f"BACK: {metrics.get('back_arch_status', 'N/A')}"
            )

        elif ex_type == "Lunges":
            text = f"BALANCE: {metrics.get('balance_status', 'N/A')}"

        else:
            text = ex_type

        cv2.putText(
            img,
            text,
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    # ---------------------------
    # Main frame processor
    # ---------------------------
    def recv(self, frame):
        try:
            image = np.asarray(
                cv2.flip(frame.to_ndarray(format="bgr24"), 1),
                dtype=np.uint8,
            )

            # Debug timestamp overlay
            cv2.putText(
                image,
                f"TS: {int(time.time())}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

            # MediaPipe expects RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_image,
            )

            timestamp_ms = int(time.time() * 1000)

            result = self._landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]

                self._draw_skeleton(image, landmarks)

                ex_type = self.get_exercise_type()

                detector = self._detectors.get(ex_type)

                if detector:
                    metrics = detector.process(landmarks)

                    metrics["pose_detected"] = True

                    self._draw_overlays(image, metrics, ex_type)

                    self.set_latest_metrics(metrics)

            else:
                self._draw_no_pose_warnings(image)

                with self._lock:
                    if self._latest_metrics is not None:
                        self._latest_metrics["pose_detected"] = False
                    else:
                        self._latest_metrics = {"pose_detected": False}

            return av.VideoFrame.from_ndarray(image, format="bgr24")

        except Exception as e:
            # Draw the exception on the frame instead of freezing
            image = np.zeros((480, 640, 3), dtype=np.uint8)

            cv2.putText(
                image,
                "PROCESSOR ERROR",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                image,
                str(e)[:60],
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            print("Video processor error:", e)

            return av.VideoFrame.from_ndarray(image, format="bgr24")