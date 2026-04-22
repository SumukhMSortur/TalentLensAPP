import os

import numpy as np
import pandas as pd
from tqdm import tqdm


class FeatureExtractor:
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

    def __init__(self, visibility_threshold=0.2):
        self.visibility_threshold = visibility_threshold

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

    @staticmethod
    def _safe_mean(values):
        valid = [value for value in values if not np.isnan(value)]
        return float(np.mean(valid)) if valid else np.nan

    @staticmethod
    def _nan_to_float(value, default=0.0):
        if value is None:
            return default
        try:
            if np.isnan(value):
                return default
        except TypeError:
            pass
        return float(value)

    def _normalize_pose_array(self, pose_data):
        array = np.asarray(pose_data, dtype=np.float32)

        if array.ndim != 3 or array.shape[1] != 33:
            raise ValueError("Expected pose data shaped as [frames, 33, channels]")

        if array.shape[2] == 3:
            visibility = np.ones((array.shape[0], array.shape[1], 1), dtype=np.float32)
            array = np.concatenate([array, visibility], axis=2)
        elif array.shape[2] > 4:
            array = array[:, :, :4]

        return array

    def _load_pose_file(self, pose_file):
        loaded = np.load(pose_file, allow_pickle=True)

        if isinstance(loaded, np.ndarray) and loaded.dtype == object and loaded.shape == ():
            loaded = loaded.item()

        if isinstance(loaded, dict) and "landmarks" in loaded:
            return self._normalize_pose_array(loaded["landmarks"])

        return self._normalize_pose_array(loaded)

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

    def _frame_metrics(self, frame_landmarks):
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
            "left_elbow_angle": left_elbow,
            "right_elbow_angle": right_elbow,
            "left_knee_angle": left_knee,
            "right_knee_angle": right_knee,
            "body_line_angle": body_line,
        }

    def _signal_columns(self, exercise_type):
        if exercise_type == "squat":
            return "left_knee_angle", "right_knee_angle"
        return "left_elbow_angle", "right_elbow_angle"

    def _build_frame_table(self, landmarks, exercise_type):
        primary_left_key, primary_right_key = self._signal_columns(exercise_type)
        rows = []

        for frame_index, frame_landmarks in enumerate(landmarks):
            metrics = self._frame_metrics(frame_landmarks)
            primary_angle = self._safe_mean(
                [metrics[primary_left_key], metrics[primary_right_key]]
            )
            symmetry = np.nan
            if not np.isnan(metrics[primary_left_key]) and not np.isnan(metrics[primary_right_key]):
                symmetry = abs(metrics[primary_left_key] - metrics[primary_right_key])

            rows.append(
                {
                    "frame_index": frame_index,
                    **metrics,
                    "primary_angle": primary_angle,
                    "symmetry_error": symmetry,
                    "valid_pose": 0 if np.isnan(primary_angle) else 1,
                }
            )

        return pd.DataFrame(rows)

    def _extract_rep_metrics(self, frame_df):
        signal = frame_df["primary_angle"].to_numpy(dtype=np.float32)
        symmetry = frame_df["symmetry_error"].to_numpy(dtype=np.float32)
        body_line = frame_df["body_line_angle"].to_numpy(dtype=np.float32)

        rep_count = 0
        rep_history = np.zeros(len(frame_df), dtype=np.int32)
        rep_details = []

        stage = "up"
        rep_start_index = None
        bottom_angle = np.inf
        bottom_index = None

        for index, angle in enumerate(signal):
            if np.isnan(angle):
                rep_history[index] = rep_count
                continue

            if angle < 90.0:
                if stage != "down":
                    rep_start_index = index
                    bottom_angle = angle
                    bottom_index = index
                stage = "down"
                if angle < bottom_angle:
                    bottom_angle = angle
                    bottom_index = index
            elif stage == "down" and angle > 160.0:
                rep_count += 1
                start = 0 if rep_start_index is None else rep_start_index
                end = index

                rep_details.append(
                    {
                        "rep_index": rep_count,
                        "start_frame": int(start),
                        "end_frame": int(end),
                        "bottom_frame": int(bottom_index if bottom_index is not None else index),
                        "bottom_angle": float(bottom_angle),
                        "top_angle": float(angle),
                        "symmetry_error_mean": self._nan_to_float(
                            np.nanmean(symmetry[start : end + 1]),
                            default=np.nan,
                        ),
                        "body_line_angle_mean": self._nan_to_float(
                            np.nanmean(body_line[start : end + 1]),
                            default=np.nan,
                        ),
                    }
                )

                stage = "up"
                rep_start_index = None
                bottom_angle = np.inf
                bottom_index = None

            rep_history[index] = rep_count

        return rep_count, rep_history, rep_details

    def extract_features(self, pose_data, action_name):
        exercise_type = self._exercise_type(action_name)
        landmarks = self._normalize_pose_array(pose_data)
        frame_df = self._build_frame_table(landmarks, exercise_type)

        rep_count, rep_history, rep_details = self._extract_rep_metrics(frame_df)
        frame_df["rep_count"] = rep_history

        rep_bottoms = np.asarray([detail["bottom_angle"] for detail in rep_details], dtype=np.float32)
        rep_tops = np.asarray([detail["top_angle"] for detail in rep_details], dtype=np.float32)
        rep_symmetry = np.asarray(
            [detail["symmetry_error_mean"] for detail in rep_details],
            dtype=np.float32,
        )
        rep_body_line = np.asarray(
            [detail["body_line_angle_mean"] for detail in rep_details],
            dtype=np.float32,
        )

        summary = {
            "average_angle": self._nan_to_float(frame_df["primary_angle"].mean(), default=np.nan),
            "min_angle": self._nan_to_float(frame_df["primary_angle"].min(), default=np.nan),
            "max_angle": self._nan_to_float(frame_df["primary_angle"].max(), default=np.nan),
            "consistency_std": self._nan_to_float(frame_df["primary_angle"].std(), default=np.nan),
            "symmetry_mean": self._nan_to_float(frame_df["symmetry_error"].mean(), default=np.nan),
            "body_line_mean": self._nan_to_float(frame_df["body_line_angle"].mean(), default=np.nan),
            "rep_depth_mean": self._nan_to_float(np.nanmean(rep_bottoms), default=np.nan),
            "rep_depth_std": self._nan_to_float(np.nanstd(rep_bottoms), default=np.nan),
            "rep_top_mean": self._nan_to_float(np.nanmean(rep_tops), default=np.nan),
            "rep_top_std": self._nan_to_float(np.nanstd(rep_tops), default=np.nan),
            "rep_symmetry_mean": self._nan_to_float(np.nanmean(rep_symmetry), default=np.nan),
            "rep_body_line_mean": self._nan_to_float(np.nanmean(rep_body_line), default=np.nan),
            "valid_frame_ratio": float(frame_df["valid_pose"].mean()) if len(frame_df) else 0.0,
        }

        return {
            "action": action_name,
            "exercise_type": exercise_type,
            "frame_count": int(len(frame_df)),
            "rep_count": int(rep_count),
            "summary": summary,
            "rep_details": rep_details,
            "frame_metrics": {
                column: frame_df[column].to_numpy(dtype=np.float32)
                for column in frame_df.columns
            },
            "frame_table": frame_df,
        }

    def _selected_lookup(self, selected_videos):
        if not selected_videos:
            return None

        lookup = set()
        for item in selected_videos:
            action = item.get("action")
            base_name = item.get("base_name")
            if action and base_name:
                lookup.add((action, base_name))
        return lookup

    def process_dataset(self, pose_path, save_path, selected_videos=None):
        os.makedirs(save_path, exist_ok=True)
        selection = self._selected_lookup(selected_videos)
        processed_features = []

        for action_name in sorted(os.listdir(pose_path)):
            action_path = os.path.join(pose_path, action_name)
            if not os.path.isdir(action_path):
                continue

            pose_files = sorted(
                [
                    file_name
                    for file_name in os.listdir(action_path)
                    if file_name.lower().endswith(".npy")
                ]
            )

            if selection is not None:
                pose_files = [
                    file_name
                    for file_name in pose_files
                    if (action_name, os.path.splitext(file_name)[0]) in selection
                ]

            if not pose_files:
                continue

            print(f"\nExtracting features for {action_name} ({len(pose_files)} file(s))")

            save_action_path = os.path.join(save_path, action_name)
            os.makedirs(save_action_path, exist_ok=True)

            for file_name in tqdm(pose_files):
                base_name = os.path.splitext(file_name)[0]
                pose_file = os.path.join(action_path, file_name)
                pose_data = self._load_pose_file(pose_file)
                feature_record = self.extract_features(pose_data, action_name)

                feature_path = os.path.join(save_action_path, base_name + ".npy")
                csv_path = os.path.join(save_action_path, base_name + ".csv")

                storage_record = {
                    key: value
                    for key, value in feature_record.items()
                    if key != "frame_table"
                }

                np.save(feature_path, storage_record, allow_pickle=True)
                feature_record["frame_table"].to_csv(csv_path, index=False)

                processed_features.append(
                    {
                        "action": action_name,
                        "base_name": base_name,
                        "feature_path": feature_path,
                        "csv_path": csv_path,
                        "rep_count": feature_record["rep_count"],
                    }
                )

        print("\nFeature extraction completed")
        return processed_features
