import os

import cv2
import mediapipe as mp
import numpy as np
from tqdm import tqdm


class PoseExtractor:
    BODY_LANDMARK_INDICES = {
        11, 12, 13, 14, 15, 16,
        23, 24, 25, 26, 27, 28,
    }
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(
        self,
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        smoothing_alpha=0.65,
        visibility_threshold=0.2,
        debug=True,
        debug_show=False,
        debug_frame_dir="outputs/debug_frames",
        debug_frame_limit=3,
    ):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.pose_connections = [
            connection
            for connection in self.mp_pose.POSE_CONNECTIONS
            if connection[0] in self.BODY_LANDMARK_INDICES
            and connection[1] in self.BODY_LANDMARK_INDICES
        ]
        self.smoothing_alpha = smoothing_alpha
        self.visibility_threshold = visibility_threshold
        self.debug = debug
        self.debug_show = debug_show
        self.debug_frame_dir = debug_frame_dir
        self.debug_frame_limit = max(int(debug_frame_limit), 0)

    @staticmethod
    def _exercise_type(action_name):
        action = action_name.lower()
        if "squat" in action:
            return "squat"
        if "push" in action:
            return "pushup"
        if "pull" in action:
            return "pullup"
        return "generic"

    @staticmethod
    def _list_video_files(action_path):
        video_extensions = (".mp4", ".avi", ".mov", ".mkv", ".mpeg", ".mpg")
        return sorted(
            file_name
            for file_name in os.listdir(action_path)
            if file_name.lower().endswith(video_extensions)
        )

    @staticmethod
    def _safe_mean(values):
        valid = [value for value in values if not np.isnan(value)]
        return float(np.mean(valid)) if valid else np.nan

    @staticmethod
    def _fourcc_to_string(fourcc_value):
        return "".join(chr((fourcc_value >> (8 * idx)) & 0xFF) for idx in range(4))

    @staticmethod
    def calculate_angle(a, b, c):
        a = np.asarray(a, dtype=np.float32)
        b = np.asarray(b, dtype=np.float32)
        c = np.asarray(c, dtype=np.float32)

        ba = a - b
        bc = c - b

        ba_norm = np.linalg.norm(ba)
        bc_norm = np.linalg.norm(bc)

        if ba_norm < 1e-6 or bc_norm < 1e-6:
            return np.nan

        cosine = np.dot(ba, bc) / (ba_norm * bc_norm)
        cosine = np.clip(cosine, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))

    def _extract_raw_landmarks(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if fps <= 0:
            fps = 24.0

        print(
            f"[DEBUG] VideoCapture read setup: path={video_path}, "
            f"fps={fps:.3f}, width={width}, height={height}"
        )

        raw_frames = []
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame is None:
                raise ValueError(f"Frame {frame_index} is None while reading {video_path}")

            if frame_index == 0:
                print(f"[DEBUG] First input frame shape: {frame.shape}")

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = self.pose.process(rgb_frame)
            rgb_frame.flags.writeable = True

            if results.pose_landmarks:
                landmarks = [
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in results.pose_landmarks.landmark
                ]
            else:
                landmarks = [[0.0, 0.0, 0.0, 0.0] for _ in range(33)]

            raw_frames.append(landmarks)
            frame_index += 1

        cap.release()

        return np.asarray(raw_frames, dtype=np.float32), {
            "fps": float(fps),
            "width": int(width),
            "height": int(height),
        }

    def _smooth_landmarks(self, raw_landmarks):
        if raw_landmarks.size == 0:
            return raw_landmarks

        smoothed = np.zeros_like(raw_landmarks)
        previous = raw_landmarks[0].copy()
        smoothed[0] = previous

        for frame_idx in range(1, len(raw_landmarks)):
            current = raw_landmarks[frame_idx].copy()
            current_valid = current[:, 3] > self.visibility_threshold
            previous_valid = previous[:, 3] > self.visibility_threshold

            blended = previous.copy()

            if np.any(current_valid):
                blended[current_valid, :3] = (
                    self.smoothing_alpha * current[current_valid, :3]
                    + (1.0 - self.smoothing_alpha) * previous[current_valid, :3]
                )
                blended[current_valid, 3] = current[current_valid, 3]

            missing_mask = ~current_valid & previous_valid
            if np.any(missing_mask):
                blended[missing_mask] = previous[missing_mask]

            new_only_mask = current_valid & ~previous_valid
            if np.any(new_only_mask):
                blended[new_only_mask] = current[new_only_mask]

            previous = blended
            smoothed[frame_idx] = blended

        return smoothed

    def _landmark_point(self, frame_landmarks, index):
        point = frame_landmarks[index]
        if point[3] <= self.visibility_threshold:
            return None
        return point[:2]

    def _midpoint(self, frame_landmarks, left_index, right_index):
        left = self._landmark_point(frame_landmarks, left_index)
        right = self._landmark_point(frame_landmarks, right_index)
        if left is None or right is None:
            return None
        return (left + right) / 2.0

    def _joint_angle(self, frame_landmarks, a_idx, b_idx, c_idx):
        a = self._landmark_point(frame_landmarks, a_idx)
        b = self._landmark_point(frame_landmarks, b_idx)
        c = self._landmark_point(frame_landmarks, c_idx)
        if a is None or b is None or c is None:
            return np.nan
        return self.calculate_angle(a, b, c)

    def _frame_angles(self, frame_landmarks):
        left_elbow = self._joint_angle(
            frame_landmarks,
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
        )
        right_elbow = self._joint_angle(
            frame_landmarks,
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
        )
        left_shoulder = self._joint_angle(
            frame_landmarks,
            self.LEFT_ELBOW,
            self.LEFT_SHOULDER,
            self.LEFT_HIP,
        )
        right_shoulder = self._joint_angle(
            frame_landmarks,
            self.RIGHT_ELBOW,
            self.RIGHT_SHOULDER,
            self.RIGHT_HIP,
        )
        left_knee = self._joint_angle(
            frame_landmarks,
            self.LEFT_HIP,
            self.LEFT_KNEE,
            self.LEFT_ANKLE,
        )
        right_knee = self._joint_angle(
            frame_landmarks,
            self.RIGHT_HIP,
            self.RIGHT_KNEE,
            self.RIGHT_ANKLE,
        )

        shoulder_mid = self._midpoint(
            frame_landmarks,
            self.LEFT_SHOULDER,
            self.RIGHT_SHOULDER,
        )
        hip_mid = self._midpoint(frame_landmarks, self.LEFT_HIP, self.RIGHT_HIP)
        ankle_mid = self._midpoint(
            frame_landmarks,
            self.LEFT_ANKLE,
            self.RIGHT_ANKLE,
        )

        body_line = np.nan
        if shoulder_mid is not None and hip_mid is not None and ankle_mid is not None:
            body_line = self.calculate_angle(shoulder_mid, hip_mid, ankle_mid)

        return {
            "left_elbow": left_elbow,
            "right_elbow": right_elbow,
            "left_shoulder": left_shoulder,
            "right_shoulder": right_shoulder,
            "left_knee": left_knee,
            "right_knee": right_knee,
            "body_line": body_line,
        }

    def _rep_signal(self, angles, exercise_type):
        if exercise_type == "squat":
            return self._safe_mean([angles["left_knee"], angles["right_knee"]])
        if exercise_type in {"pushup", "pullup"}:
            return self._safe_mean([angles["left_elbow"], angles["right_elbow"]])
        return np.nan

    def _count_reps(self, signal_values, exercise_type):
        if exercise_type not in {"squat", "pushup", "pullup"}:
            return 0, np.zeros(len(signal_values), dtype=np.int32), ["unknown"] * len(signal_values)

        rep_count = 0
        rep_history = np.zeros(len(signal_values), dtype=np.int32)
        stage = "up"
        stage_history = []

        for index, signal in enumerate(signal_values):
            if np.isnan(signal):
                rep_history[index] = rep_count
                stage_history.append(stage)
                continue

            if signal < 90.0:
                stage = "down"
            elif stage == "down" and signal > 160.0:
                rep_count += 1
                stage = "up"

            rep_history[index] = rep_count
            stage_history.append(stage)

        return rep_count, rep_history, stage_history

    def _to_pixel(self, point, frame_width, frame_height):
        x = int(np.clip(point[0] * frame_width, 0, frame_width - 1))
        y = int(np.clip(point[1] * frame_height, 0, frame_height - 1))
        return x, y

    def _draw_pose(self, frame, frame_landmarks, status_color=None):
        landmark_color = status_color if status_color is not None else (0, 255, 0)
        connection_color = (0, 200, 255) if status_color is None else status_color
        frame_height, frame_width = frame.shape[:2]
        compact_mode = frame_width <= 480 or frame_height <= 320
        line_thickness = 2 if compact_mode else 3
        circle_radius = 4 if compact_mode else 5

        for start_index, end_index in self.pose_connections:
            start_point = frame_landmarks[start_index]
            end_point = frame_landmarks[end_index]
            if (
                start_point[3] <= self.visibility_threshold
                or end_point[3] <= self.visibility_threshold
            ):
                continue

            start_px = self._to_pixel(start_point[:2], frame_width, frame_height)
            end_px = self._to_pixel(end_point[:2], frame_width, frame_height)
            cv2.line(
                frame,
                start_px,
                end_px,
                connection_color,
                line_thickness,
                cv2.LINE_AA,
            )

        for landmark_index in self.BODY_LANDMARK_INDICES:
            landmark = frame_landmarks[landmark_index]
            if landmark[3] <= self.visibility_threshold:
                continue

            center = self._to_pixel(landmark[:2], frame_width, frame_height)
            cv2.circle(
                frame,
                center,
                circle_radius,
                landmark_color,
                -1,
                cv2.LINE_AA,
            )
            cv2.circle(
                frame,
                center,
                max(circle_radius + 1, 2),
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def _draw_angle_label(
        self,
        frame,
        frame_landmarks,
        joint_index,
        angle_value,
        label,
        color=(255, 255, 255),
    ):
        if np.isnan(angle_value):
            return

        joint_point = frame_landmarks[joint_index]
        if joint_point[3] <= self.visibility_threshold:
            return

        frame_height, frame_width = frame.shape[:2]
        px, py = self._to_pixel(joint_point[:2], frame_width, frame_height)
        compact_mode = frame_width <= 480 or frame_height <= 320
        font_scale = 0.18 if compact_mode else 0.34
        thickness = 1
        shadow_thickness = 2 if compact_mode else 3
        x_offset = 3 if compact_mode else 6
        y_offset = 3 if compact_mode else 6
        text_position = (px + x_offset, py - y_offset)
        label_text = f"{label}: {int(round(angle_value))}"

        cv2.putText(
            frame,
            label_text,
            text_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (20, 20, 20),
            shadow_thickness,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            label_text,
            text_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def _status_color(status_name):
        if status_name == "good":
            return (70, 190, 120)
        if status_name == "warning":
            return (0, 196, 255)
        if status_name == "bad":
            return (64, 64, 255)
        return (0, 255, 0)

    @staticmethod
    def _draw_panel(frame, x1, y1, x2, y2, border_color, alpha=0.72):
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (18, 18, 18), -1)
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)

    @staticmethod
    def _short_action_name(predicted_label):
        if not predicted_label:
            return None
        tokens = str(predicted_label).replace("-", " ").split()
        if len(tokens) <= 2:
            return " ".join(token.title() for token in tokens)
        return " ".join(token.title() for token in tokens[:2])

    @staticmethod
    def _wrap_text(message, limit=24):
        words = str(message).split()
        lines = []
        current = []
        current_len = 0

        for word in words:
            projected = current_len + len(word) + (1 if current else 0)
            if current and projected > limit:
                lines.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len = projected

        if current:
            lines.append(" ".join(current))
        return lines[:2]

    def _draw_header(
        self,
        frame,
        exercise_type,
        rep_count,
        stage_name,
        predicted_label=None,
        prediction_confidence=None,
        status_name="neutral",
    ):
        border_color = self._status_color(status_name)
        frame_height, frame_width = frame.shape[:2]
        compact_mode = frame_width <= 480 or frame_height <= 320

        x1 = 12
        y1 = 12
        panel_width = min(int(frame_width * 0.34), 142 if compact_mode else 320)
        panel_height = 54 if compact_mode else 118
        x2 = min(x1 + panel_width, frame_width - 12)
        y2 = min(y1 + panel_height, frame_height - 12)

        title_scale = 0.24 if compact_mode else 0.7
        body_scale = 0.24 if compact_mode else 0.62
        sub_scale = 0.22 if compact_mode else 0.55
        title_y = y1 + (16 if compact_mode else 30)
        row_2_y = y1 + (30 if compact_mode else 58)
        row_3_y = y1 + (42 if compact_mode else 84)
        row_4_y = y1 + (51 if compact_mode else 108)

        self._draw_panel(frame, x1, y1, x2, y2, border_color)

        cv2.putText(
            frame,
            "TalentLens",
            (x1 + 12, title_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            title_scale,
            (255, 255, 255),
            1 if compact_mode else 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"{exercise_type.title()}  {rep_count} reps" if compact_mode else f"{exercise_type.title()}  Reps {rep_count}",
            (x1 + 12, row_2_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            body_scale,
            (255, 255, 255),
            1 if compact_mode else 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Stage {stage_name[0].upper()}" if compact_mode else f"Stage {stage_name.title()}",
            (x1 + 12, row_3_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            body_scale,
            (255, 255, 255),
            1 if compact_mode else 2,
            cv2.LINE_AA,
        )
        if predicted_label:
            prediction_text = f"{self._short_action_name(predicted_label)}"
            if prediction_confidence is not None:
                prediction_text += f" {prediction_confidence:.0%}" if compact_mode else f" {prediction_confidence:.0%}"
            cv2.putText(
                frame,
                prediction_text,
                (x1 + 12, row_4_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                sub_scale,
                border_color,
                1 if compact_mode else 2,
                cv2.LINE_AA,
            )

    def _draw_feedback_panel(self, frame, feedback_entry):
        if not feedback_entry:
            return

        status_name = feedback_entry.get("status", "neutral")
        issues = feedback_entry.get("issues") or []
        posture_error = feedback_entry.get("posture_error")
        similarity = feedback_entry.get("similarity")
        border_color = self._status_color(status_name)

        frame_height, frame_width = frame.shape[:2]
        compact_mode = frame_width <= 480 or frame_height <= 320
        panel_width = min(int(frame_width * 0.3), 126 if compact_mode else 280)
        panel_height = 56 if compact_mode else 132
        x2 = frame_width - 12
        x1 = max(x2 - panel_width, 12)
        y1 = frame_height - panel_height - 12 if compact_mode else 12
        y2 = min(y1 + panel_height, frame_height - 12)

        title_scale = 0.24 if compact_mode else 0.62
        body_scale = 0.24 if compact_mode else 0.55
        meta_scale = 0.22 if compact_mode else 0.52
        line_gap = 15 if compact_mode else 22

        self._draw_panel(frame, x1, y1, x2, y2, border_color)
        cv2.putText(
            frame,
            status_name.title(),
            (x1 + 8, y1 + 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            title_scale,
            border_color,
            1 if compact_mode else 2,
            cv2.LINE_AA,
        )

        if similarity is not None:
            cv2.putText(
                frame,
                f"Sim {similarity:.0f}%",
                (x1 + 8, y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                body_scale,
                (255, 255, 255),
                1 if compact_mode else 2,
                cv2.LINE_AA,
            )

        if posture_error is not None and not compact_mode:
            cv2.putText(
                frame,
                f"Posture err {posture_error:.1f} deg",
                (x1 + 10, y1 + 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                meta_scale,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )

        issue_lines = issues[:3] if issues else ["Form aligned with reference"]
        wrapped_lines = []
        for message in issue_lines[:1] if compact_mode else issue_lines[:2]:
            wrapped_lines.extend(self._wrap_text(message, limit=22 if compact_mode else 30))

        for issue_index, message in enumerate(wrapped_lines[:1] if compact_mode else wrapped_lines[:2]):
            cv2.putText(
                frame,
                message[:34] if compact_mode else message[:48],
                (x1 + 8, y1 + (45 if compact_mode else 78) + issue_index * line_gap),
                cv2.FONT_HERSHEY_SIMPLEX,
                meta_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def _save_debug_frame(self, output_path, frame_index, frame):
        if frame_index >= self.debug_frame_limit:
            return

        base_name = os.path.splitext(os.path.basename(output_path))[0]
        target_dir = os.path.join(self.debug_frame_dir, base_name)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"frame_{frame_index:04d}.jpg")
        cv2.imwrite(target_path, frame)
        print(f"[DEBUG] Saved annotated frame preview: {target_path}")

    def _open_video_writer(self, output_path, fps, frame_size):
        codec_candidates = ["avc1", "H264", "mp4v", "XVID", "MJPG"]

        for codec_name in codec_candidates:
            fourcc = cv2.VideoWriter_fourcc(*codec_name)
            writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
            if writer.isOpened():
                print(
                    f"[DEBUG] VideoWriter opened: path={output_path}, codec={codec_name}, "
                    f"fps={fps:.3f}, size={frame_size}"
                )
                return writer, codec_name
            writer.release()

        raise ValueError(
            f"Cannot open output video writer for {output_path}. "
            f"Tried codecs: {', '.join(codec_candidates)}"
        )

    def _validate_written_video(self, output_path, expected_size):
        cap = cv2.VideoCapture(output_path)
        if not cap.isOpened():
            raise ValueError(f"Output video could not be reopened: {output_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            raise ValueError(f"Output video has no readable frames: {output_path}")

        actual_size = (width, height)
        if actual_size != expected_size:
            raise ValueError(
                f"Output size mismatch for {output_path}: expected={expected_size}, actual={actual_size}"
            )

        print(
            f"[DEBUG] Output validation: path={output_path}, "
            f"size={actual_size}, fourcc={self._fourcc_to_string(fourcc)!r}, "
            f"first_frame_shape={frame.shape}"
        )

    def _write_annotated_video(
        self,
        video_path,
        output_path,
        landmarks,
        angle_sequence,
        rep_history,
        stage_history,
        exercise_type,
        video_meta,
        comparison_feedback=None,
        predicted_label=None,
        prediction_confidence=None,
    ):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fps = video_meta["fps"] if video_meta["fps"] > 0 else 24.0
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot reopen video for annotation: {video_path}")

        writer = None
        frame_index = 0
        written_frames = 0
        frame_size = None

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame is None:
                    raise ValueError(f"Read an empty frame while annotating {video_path}")
                if frame_index >= len(landmarks):
                    break

                if frame_index == 0:
                    print(f"[DEBUG] First annotated frame shape before write: {frame.shape}")

                frame_height, frame_width = frame.shape[:2]
                current_frame_size = (int(frame_width), int(frame_height))
                if frame_size is None:
                    frame_size = current_frame_size
                    writer, _ = self._open_video_writer(output_path, fps, frame_size)
                elif current_frame_size != frame_size:
                    frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_LINEAR)

                annotated_frame = frame.copy()
                frame_landmarks = landmarks[frame_index]
                angles = angle_sequence[frame_index]
                stage_name = (
                    stage_history[frame_index] if frame_index < len(stage_history) else "unknown"
                )
                feedback_entry = None
                if comparison_feedback and frame_index < len(comparison_feedback):
                    feedback_entry = comparison_feedback[frame_index]

                status_name = "neutral" if feedback_entry is None else feedback_entry.get("status", "neutral")
                joint_statuses = {} if feedback_entry is None else feedback_entry.get("joint_statuses", {})
                skeleton_color = None if feedback_entry is None else self._status_color(status_name)

                self._draw_pose(annotated_frame, frame_landmarks, status_color=skeleton_color)
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.LEFT_ELBOW,
                    angles["left_elbow"],
                    "LE",
                    color=self._status_color(joint_statuses.get("left_elbow", "neutral")),
                )
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.RIGHT_ELBOW,
                    angles["right_elbow"],
                    "RE",
                    color=self._status_color(joint_statuses.get("right_elbow", "neutral")),
                )
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.LEFT_SHOULDER,
                    angles["left_shoulder"],
                    "LS",
                    color=self._status_color(joint_statuses.get("left_shoulder", "neutral")),
                )
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.RIGHT_SHOULDER,
                    angles["right_shoulder"],
                    "RS",
                    color=self._status_color(joint_statuses.get("right_shoulder", "neutral")),
                )
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.LEFT_KNEE,
                    angles["left_knee"],
                    "LK",
                    color=self._status_color(joint_statuses.get("left_knee", "neutral")),
                )
                self._draw_angle_label(
                    annotated_frame,
                    frame_landmarks,
                    self.RIGHT_KNEE,
                    angles["right_knee"],
                    "RK",
                    color=self._status_color(joint_statuses.get("right_knee", "neutral")),
                )
                self._draw_header(
                    annotated_frame,
                    exercise_type,
                    int(rep_history[frame_index]),
                    stage_name,
                    predicted_label=predicted_label,
                    prediction_confidence=prediction_confidence,
                    status_name=status_name,
                )
                self._draw_feedback_panel(annotated_frame, feedback_entry)

                if self.debug:
                    self._save_debug_frame(output_path, frame_index, annotated_frame)

                if self.debug_show:
                    cv2.imshow("Annotated Output Debug", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.debug_show = False

                writer.write(annotated_frame)
                written_frames += 1

                if frame_index < 3 or frame_index % 100 == 0:
                    print(
                        f"[DEBUG] Wrote frame {frame_index}: shape={annotated_frame.shape}, "
                        f"reps={rep_history[frame_index]}, stage={stage_name}"
                    )

                frame_index += 1
        finally:
            cap.release()
            if writer is not None:
                writer.release()
            if self.debug_show:
                cv2.destroyAllWindows()

        if written_frames == 0:
            raise ValueError(f"No frames were written to {output_path}")

        self._validate_written_video(output_path, frame_size)

        return {
            "written_frames": int(written_frames),
            "fps": float(fps),
            "frame_size": frame_size,
        }

    def compute_joint_angles(self, landmarks):
        return [self._frame_angles(frame) for frame in np.asarray(landmarks, dtype=np.float32)]

    def annotate_video(
        self,
        video_path,
        output_path,
        landmarks,
        angle_sequence,
        rep_history,
        stage_history,
        exercise_type,
        video_meta,
        comparison_feedback=None,
        predicted_label=None,
        prediction_confidence=None,
    ):
        return self._write_annotated_video(
            video_path=video_path,
            output_path=output_path,
            landmarks=landmarks,
            angle_sequence=angle_sequence,
            rep_history=rep_history,
            stage_history=stage_history,
            exercise_type=exercise_type,
            video_meta=video_meta,
            comparison_feedback=comparison_feedback,
            predicted_label=predicted_label,
            prediction_confidence=prediction_confidence,
        )

    def extract_video(self, video_path, pose_output_path, annotated_video_path, action_name):
        raw_landmarks, video_meta = self._extract_raw_landmarks(video_path)
        smoothed_landmarks = self._smooth_landmarks(raw_landmarks)
        exercise_type = self._exercise_type(action_name)

        angle_sequence = [self._frame_angles(frame) for frame in smoothed_landmarks]
        signal_values = np.asarray(
            [self._rep_signal(angles, exercise_type) for angles in angle_sequence],
            dtype=np.float32,
        )
        rep_count, rep_history, stage_history = self._count_reps(
            signal_values,
            exercise_type,
        )

        np.save(pose_output_path, smoothed_landmarks)

        write_summary = self._write_annotated_video(
            video_path=video_path,
            output_path=annotated_video_path,
            landmarks=smoothed_landmarks,
            angle_sequence=angle_sequence,
            rep_history=rep_history,
            stage_history=stage_history,
            exercise_type=exercise_type,
            video_meta=video_meta,
        )

        return {
            "action": action_name,
            "exercise_type": exercise_type,
            "video_path": video_path,
            "pose_path": pose_output_path,
            "output_video_path": annotated_video_path,
            "frame_count": int(len(smoothed_landmarks)),
            "rep_count": int(rep_count),
            "written_frames": write_summary["written_frames"],
        }

    def extract_dataset(
        self,
        dataset_path,
        save_path,
        output_root="outputs/pose_samples",
        limit_per_action=2,
    ):
        os.makedirs(save_path, exist_ok=True)
        os.makedirs(output_root, exist_ok=True)

        processed_videos = []

        for action_name in sorted(os.listdir(dataset_path)):
            action_path = os.path.join(dataset_path, action_name)
            if not os.path.isdir(action_path):
                continue

            video_files = self._list_video_files(action_path)
            if limit_per_action is not None:
                video_files = video_files[:limit_per_action]

            if not video_files:
                print(f"\nSkipping {action_name}: no supported videos found")
                continue

            print(f"\nExtracting poses for {action_name} ({len(video_files)} video(s))")

            pose_action_path = os.path.join(save_path, action_name)
            output_action_path = os.path.join(output_root, action_name)
            os.makedirs(pose_action_path, exist_ok=True)
            os.makedirs(output_action_path, exist_ok=True)

            for video_file in tqdm(video_files):
                base_name = os.path.splitext(video_file)[0]
                video_path = os.path.join(action_path, video_file)
                pose_output_path = os.path.join(pose_action_path, base_name + ".npy")
                annotated_video_path = os.path.join(output_action_path, base_name + ".mp4")

                record = self.extract_video(
                    video_path=video_path,
                    pose_output_path=pose_output_path,
                    annotated_video_path=annotated_video_path,
                    action_name=action_name,
                )
                record["base_name"] = base_name
                processed_videos.append(record)

        print("\nPose extraction completed")
        return processed_videos

    def run(
        self,
        dataset_path,
        save_path="dataset/poses",
        output_root="outputs/pose_samples",
        limit_per_action=2,
    ):
        return self.extract_dataset(
            dataset_path=dataset_path,
            save_path=save_path,
            output_root=output_root,
            limit_per_action=limit_per_action,
        )
