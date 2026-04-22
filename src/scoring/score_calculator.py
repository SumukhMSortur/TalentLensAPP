import os

import numpy as np


class ScoreCalculator:
    def __init__(self):
        pass

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
    def _clip_score(value):
        return float(np.clip(value, 0.0, 100.0))

    @staticmethod
    def _nan_safe(value, default=np.nan):
        if value is None:
            return default
        try:
            if np.isnan(value):
                return default
        except TypeError:
            pass
        return float(value)

    def _load_feature_file(self, feature_file):
        loaded = np.load(feature_file, allow_pickle=True)

        if isinstance(loaded, np.ndarray) and loaded.dtype == object and loaded.shape == ():
            loaded = loaded.item()

        if isinstance(loaded, dict):
            return loaded

        raise ValueError(f"Unsupported feature format in {feature_file}")

    def _scoring_profile(self, exercise_type):
        if exercise_type == "squat":
            return {
                "depth_target": 90.0,
                "top_target": 170.0,
                "body_line_target": 155.0,
            }
        if exercise_type == "pushup":
            return {
                "depth_target": 90.0,
                "top_target": 170.0,
                "body_line_target": 175.0,
            }
        if exercise_type == "pullup":
            return {
                "depth_target": 85.0,
                "top_target": 170.0,
                "body_line_target": 165.0,
            }
        return {
            "depth_target": 90.0,
            "top_target": 170.0,
            "body_line_target": 170.0,
        }

    def calculate_score(self, feature_record):
        exercise_type = feature_record.get("exercise_type") or self._exercise_type(
            feature_record.get("action", "")
        )
        summary = feature_record["summary"]
        profile = self._scoring_profile(exercise_type)

        rep_count = int(feature_record.get("rep_count", 0))
        valid_frame_ratio = self._nan_safe(summary.get("valid_frame_ratio"), default=0.0)

        depth_value = self._nan_safe(summary.get("rep_depth_mean"), default=summary.get("min_angle"))
        top_value = self._nan_safe(summary.get("rep_top_mean"), default=summary.get("max_angle"))
        body_line_value = self._nan_safe(
            summary.get("rep_body_line_mean"),
            default=summary.get("body_line_mean"),
        )
        consistency_depth = self._nan_safe(
            summary.get("rep_depth_std"),
            default=summary.get("consistency_std"),
        )
        consistency_top = self._nan_safe(
            summary.get("rep_top_std"),
            default=summary.get("consistency_std"),
        )
        symmetry_value = self._nan_safe(
            summary.get("rep_symmetry_mean"),
            default=summary.get("symmetry_mean"),
        )

        depth_score = self._clip_score(100.0 - abs(depth_value - profile["depth_target"]) * 1.5)
        extension_score = self._clip_score(100.0 - abs(top_value - profile["top_target"]) * 1.2)
        posture_score = self._clip_score(100.0 - abs(body_line_value - profile["body_line_target"]) * 1.0)
        form_score = self._clip_score(0.6 * extension_score + 0.4 * posture_score)

        consistency_penalty = consistency_depth * 1.8 + consistency_top * 0.7
        consistency_score = self._clip_score(100.0 - consistency_penalty)
        symmetry_score = self._clip_score(100.0 - symmetry_value * 1.5)

        rep_bonus = 1.0 if rep_count > 0 else 0.35
        reliability_scale = np.clip(0.55 + 0.45 * valid_frame_ratio, 0.0, 1.0)

        raw_score = (
            0.35 * depth_score
            + 0.25 * form_score
            + 0.20 * consistency_score
            + 0.20 * symmetry_score
        )
        final_score = self._clip_score(raw_score * rep_bonus * reliability_scale)

        return {
            "exercise_type": exercise_type,
            "rep_count": rep_count,
            "depth_score": round(depth_score, 2),
            "form_score": round(form_score, 2),
            "consistency_score": round(consistency_score, 2),
            "symmetry_score": round(symmetry_score, 2),
            "valid_frame_ratio": round(valid_frame_ratio, 3),
            "final_score": round(final_score, 2),
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

    def process_dataset(self, feature_path, selected_videos=None):
        selection = self._selected_lookup(selected_videos)
        results = []

        for action_name in sorted(os.listdir(feature_path)):
            action_path = os.path.join(feature_path, action_name)
            if not os.path.isdir(action_path):
                continue

            feature_files = sorted(
                [
                    file_name
                    for file_name in os.listdir(action_path)
                    if file_name.lower().endswith(".npy")
                ]
            )

            if selection is not None:
                feature_files = [
                    file_name
                    for file_name in feature_files
                    if (action_name, os.path.splitext(file_name)[0]) in selection
                ]

            if not feature_files:
                continue

            print(f"\nScoring {action_name} ({len(feature_files)} file(s))")

            for file_name in feature_files:
                base_name = os.path.splitext(file_name)[0]
                feature_file = os.path.join(action_path, file_name)
                feature_record = self._load_feature_file(feature_file)
                score_details = self.calculate_score(feature_record)

                result = {
                    "action": action_name,
                    "base_name": base_name,
                    "feature_path": feature_file,
                    **score_details,
                }
                results.append(result)

                print(f"\nVideo: {action_name}/{base_name}")
                print(f"Reps: {result['rep_count']}")
                print(f"Depth Score      : {result['depth_score']}")
                print(f"Form Score       : {result['form_score']}")
                print(f"Consistency Score: {result['consistency_score']}")
                print(f"Symmetry Score   : {result['symmetry_score']}")
                print(f"Final Score      : {result['final_score']}")

        return results
