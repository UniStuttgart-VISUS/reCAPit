import shapely
import numpy as np
import mediapipe as mp
import cv2 as cv
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2


def envelopes_from_landmarks(hand_landmark_list, size):
    for idx in range(len(hand_landmark_list)):
        hand_landmarks = hand_landmark_list[idx]
        points = [(landmark.x*size[1], landmark.y*size[0]) for landmark in hand_landmarks]
        yield shapely.MultiPoint(points).bounds


def mask_from_hand_landmarks(detection_result, size):
    hand_landmark_list = detection_result.hand_landmarks
    hand_mask = np.zeros(size, dtype=bool)

    for (min_x, min_y, max_x, max_y) in envelopes_from_landmarks(hand_landmark_list, size):
        hand_mask[int(min_y): int(max_y), int(min_x): int(max_x)] = True
    return hand_mask


def draw_landmarks_on_image(rgb_image, detection_result):
    MARGIN = 10  # pixels
    FONT_SIZE = 1
    FONT_THICKNESS = 1
    HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_image = np.copy(rgb_image)

    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]

        # Draw the hand landmarks.
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
        landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
        annotated_image,
        hand_landmarks_proto,
        solutions.hands.HAND_CONNECTIONS,
        solutions.drawing_styles.get_default_hand_landmarks_style(),
        solutions.drawing_styles.get_default_hand_connections_style())

        # Get the top left corner of the detected hand's bounding box.
        height, width, _ = annotated_image.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN

        # Draw handedness (left or right hand) on the image.
        cv.putText(annotated_image, f"{handedness[0].category_name}",
                    (text_x, text_y), cv.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv.LINE_AA)

    return annotated_image


def create_hand_landmarker(num_hands, model_asset_path):
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_asset_path),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=num_hands,
        min_hand_detection_confidence=.05)

    return HandLandmarker.create_from_options(options) 


class HandDetector:
    def __init__(self, num_hands, model_asset_path) -> None:
        self.landmarker = create_hand_landmarker(num_hands, model_asset_path)

    def detect(self, img, pos_msec):
        img_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv.cvtColor(img, cv.COLOR_BGR2RGB))
        return self.landmarker.detect_for_video(img_mp, pos_msec)