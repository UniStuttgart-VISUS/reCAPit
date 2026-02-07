import cv2
import numpy as np
from pupil_apriltags import Detector
from utils import draw_tags


class MarkerMapper:
    def __init__(self, ref_tags: list, ref_size:tuple[float, float]) -> None:
        self.ref_tags = {str(t.tag_id): t for t in ref_tags}
        self.curr_transform = None
        self.ref_size = ref_size

    def on_surface(self, x: float, y: float) -> bool:
        return 0 <= x < self.ref_size[0] and 0 <= y < self.ref_size[1]

    def map_coord(self, src_x: float, src_y: float) -> tuple[float, float]:
        if self.curr_transform is None:
            raise ValueError

        mx, my, mz = self.curr_transform @ np.array([src_x, src_y, 1.0])
        mx = mx / mz
        my = my / mz
        return mx, my

    def map_frame(self, img:np.ndarray) -> np.ndarray:
        return cv2.warpPerspective(img, self.curr_transform, self.ref_size)

    def get_curr_transform(self) -> np.ndarray:
        return self.curr_transform

    def update_transform(self, src_tags: list) -> tuple[bool, int]:
        src_coord_list = []
        dst_coord_list = []

        detected_marker_count = 0

        for src in src_tags:
            tag_id = str(src.tag_id)

            if tag_id in self.ref_tags:
                ref = self.ref_tags[tag_id]
                detected_marker_count += 1

                src_coord_list.extend(src.corners)
                dst_coord_list.extend(ref.corners)

        # At least four correspondences are needed to compute homography
        if len(src_coord_list) < 4 or len(dst_coord_list) < 4:
            return False, detected_marker_count

        src_coord_list = np.array(src_coord_list, np.float32)
        dst_coord_list = np.array(dst_coord_list, np.float32)

        self.curr_transform, _ = cv2.findHomography(src_coord_list, dst_coord_list)
        return True, detected_marker_count

    @staticmethod
    def find_reference_tags(video_path: str, at_detector: Detector,
                            min_tags: int, max_trials: int,
                            show_output=False) -> list:

        if max_trials <= 0:
            msg = 'max_trials must be strictly greater than zero'
            raise ValueError(msg)

        tags = []
        cap = cv2.VideoCapture(video_path)

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        trials = 0

        while cap.isOpened() and trials < max_trials:
            ret, img = cap.read()
            if not ret:
                break

            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            tags = at_detector.detect(img_gray)

            if show_output:
                draw_tags(img, tags)
                cv2.imshow("frame", img)
                if 0xff & cv2.waitKey(0) == ord('q'):
                    break
            if len(tags) >= min_tags:
                break
            trials += 1
        else:
            if trials >= max_trials:
                msg = f'Failed to find at least {min_tags} tag(s) in the first {max_trials} frame(s) of the reference video'
            else:
                msg = f'Video ended after {trials} frame(s) without finding at least {min_tags} tag(s)'

            raise RuntimeError(msg)

        cv2.destroyAllWindows()
        cap.release()
        return tags, (frame_width, frame_height)