from pathlib import Path

import numpy as np

from src.analytics.model_performance import ModelPerformanceAnalyzer
from src.features.feature_extractor import FeatureExtractor
from src.pose.pose_extractor import PoseExtractor
from src.scoring.score_calculator import ScoreCalculator


ANGLE_KEYS = [
    "left_elbow",
    "right_elbow",
    "left_shoulder",
    "right_shoulder",
    "left_knee",
    "right_knee",
    "body_line",
]

DISPLAY_NAME_LOOKUP = {
    "left_elbow": "Left arm angle too low",
    "right_elbow": "Right arm angle too low",
    "left_shoulder": "Left shoulder alignment needs work",
    "right_shoulder": "Right shoulder alignment needs work",
    "left_knee": "Left knee not aligned",
    "right_knee": "Right knee not aligned",
    "body_line": "Torso line is inconsistent",
}


def _safe_nanmean(values, default=np.nan):
    values = np.asarray(values, dtype=np.float32)
    if values.size == 0:
        return float(default)
    valid = values[~np.isnan(values)]
    if valid.size == 0:
        return float(default)
    return float(np.mean(valid))


def _fill_nan_columns(matrix):
    array = np.asarray(matrix, dtype=np.float32).copy()
    if array.ndim != 2:
        raise ValueError("Expected a [frames, features] array.")
    if array.size == 0:
        return array

    for column_index in range(array.shape[1]):
        column = array[:, column_index]
        valid_mask = ~np.isnan(column)
        if np.any(valid_mask):
            array[:, column_index] = np.where(valid_mask, column, np.nanmean(column[valid_mask]))
        else:
            array[:, column_index] = 0.0
    return array


def _resample_sequence(matrix, target_length):
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.shape[0] == target_length:
        return matrix
    if matrix.shape[0] == 0:
        return np.zeros((target_length, matrix.shape[1]), dtype=np.float32)
    if matrix.shape[0] == 1:
        return np.repeat(matrix, target_length, axis=0)

    original_index = np.linspace(0.0, 1.0, num=matrix.shape[0], dtype=np.float32)
    target_index = np.linspace(0.0, 1.0, num=target_length, dtype=np.float32)
    columns = [
        np.interp(target_index, original_index, matrix[:, column_index])
        for column_index in range(matrix.shape[1])
    ]
    return np.stack(columns, axis=1).astype(np.float32)


def _downsample_for_dtw(matrix, max_frames=180):
    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.shape[0] <= max_frames:
        return matrix
    index = np.linspace(0, matrix.shape[0] - 1, num=max_frames, dtype=np.int32)
    return matrix[index]


def _dtw_distance(seq1, seq2):
    len_a = seq1.shape[0]
    len_b = seq2.shape[0]
    table = np.full((len_a + 1, len_b + 1), np.inf, dtype=np.float32)
    table[0, 0] = 0.0

    for index_a in range(1, len_a + 1):
        for index_b in range(1, len_b + 1):
            local_cost = float(np.linalg.norm(seq1[index_a - 1] - seq2[index_b - 1]))
            table[index_a, index_b] = local_cost + min(
                table[index_a - 1, index_b],
                table[index_a, index_b - 1],
                table[index_a - 1, index_b - 1],
            )
    return float(table[len_a, len_b] / max(len_a + len_b, 1))


def _angle_matrix(angle_sequence):
    rows = []
    for angle_row in angle_sequence:
        rows.append([angle_row.get(key, np.nan) for key in ANGLE_KEYS])
    if not rows:
        return np.zeros((0, len(ANGLE_KEYS)), dtype=np.float32)
    return _fill_nan_columns(np.asarray(rows, dtype=np.float32))


def compute_joint_angles(landmarks, pose_extractor=None):
    extractor = pose_extractor or PoseExtractor(debug=False)
    return extractor.compute_joint_angles(landmarks)


def calculate_similarity(seq1, seq2):
    angle_matrix_1 = _angle_matrix(seq1)
    angle_matrix_2 = _angle_matrix(seq2)

    if angle_matrix_1.size == 0 or angle_matrix_2.size == 0:
        return {
            "score": 0.0,
            "dtw_score": 0.0,
            "cosine_score": 0.0,
        }

    aligned_length = min(max(angle_matrix_1.shape[0], angle_matrix_2.shape[0]), 180)
    aligned_1 = _resample_sequence(angle_matrix_1, aligned_length)
    aligned_2 = _resample_sequence(angle_matrix_2, aligned_length)

    flattened_1 = aligned_1.reshape(-1)
    flattened_2 = aligned_2.reshape(-1)
    denom = float(np.linalg.norm(flattened_1) * np.linalg.norm(flattened_2))
    cosine_similarity = 0.0 if denom < 1e-8 else float(np.dot(flattened_1, flattened_2) / denom)
    cosine_score = float(np.clip((cosine_similarity + 1.0) * 50.0, 0.0, 100.0))

    dtw_input_1 = _downsample_for_dtw(aligned_1)
    dtw_input_2 = _downsample_for_dtw(aligned_2)
    dtw_distance = _dtw_distance(dtw_input_1, dtw_input_2)
    dtw_score = float(np.clip(100.0 - dtw_distance * 1.15, 0.0, 100.0))

    final_score = round(0.65 * dtw_score + 0.35 * cosine_score, 2)
    return {
        "score": final_score,
        "dtw_score": round(dtw_score, 2),
        "cosine_score": round(cosine_score, 2),
    }


def compare_sequences(seq1, seq2):
    angle_matrix_1 = _angle_matrix(seq1)
    angle_matrix_2 = _angle_matrix(seq2)
    similarity = calculate_similarity(seq1, seq2)

    if angle_matrix_1.size == 0 or angle_matrix_2.size == 0:
        return {
            "similarity_score": 0.0,
            "label": "Needs Improvement",
            "frame_wise_deviation": np.zeros(0, dtype=np.float32),
            "average_posture_error": 0.0,
            "joint_angle_difference": 0.0,
            "movement_smoothness": 0.0,
            "temporal_consistency": 0.0,
            "per_joint_error": {key: 0.0 for key in ANGLE_KEYS},
            "feedback_messages": ["Unable to compare because one sequence had no valid pose frames"],
            "frame_feedback": [],
            "aligned_length": 0,
            "dtw_score": 0.0,
            "cosine_score": 0.0,
        }

    aligned_length = min(max(angle_matrix_1.shape[0], angle_matrix_2.shape[0]), 180)
    aligned_1 = _resample_sequence(angle_matrix_1, aligned_length)
    aligned_2 = _resample_sequence(angle_matrix_2, aligned_length)
    deviations = np.abs(aligned_1 - aligned_2)
    frame_deviation = np.mean(deviations, axis=1)
    average_posture_error = float(np.mean(frame_deviation)) if frame_deviation.size else 0.0
    per_joint_error = {
        key: float(np.mean(deviations[:, index]))
        for index, key in enumerate(ANGLE_KEYS)
    }

    smoothness_signal = np.mean(aligned_2[:, [0, 1, 4, 5]], axis=1)
    if smoothness_signal.shape[0] >= 3:
        acceleration = np.diff(smoothness_signal, n=2)
        movement_smoothness = float(np.clip(100.0 - np.std(acceleration) * 3.5, 0.0, 100.0))
    else:
        movement_smoothness = 0.0

    temporal_consistency = float(np.clip(100.0 - np.std(frame_deviation) * 1.6, 0.0, 100.0))
    label = "Good Form" if similarity["score"] >= 75.0 else "Needs Improvement"

    top_issue_keys = sorted(per_joint_error, key=per_joint_error.get, reverse=True)
    feedback_messages = [
        DISPLAY_NAME_LOOKUP[key]
        for key in top_issue_keys
        if per_joint_error[key] >= 12.0
    ][:3]
    if not feedback_messages:
        feedback_messages = ["Posture is close to the reference video"]

    frame_feedback = []
    similarity_score = similarity["score"]
    for frame_index in range(aligned_length):
        joint_statuses = {}
        frame_error = float(frame_deviation[frame_index])
        if frame_error <= 8.0:
            status_name = "good"
        elif frame_error <= 15.0:
            status_name = "warning"
        else:
            status_name = "bad"

        issues = []
        for joint_index, key in enumerate(ANGLE_KEYS):
            deviation = float(deviations[frame_index, joint_index])
            if deviation <= 8.0:
                joint_statuses[key] = "good"
            elif deviation <= 15.0:
                joint_statuses[key] = "warning"
            else:
                joint_statuses[key] = "bad"
                if len(issues) < 2:
                    issues.append(DISPLAY_NAME_LOOKUP[key])

        if not issues:
            issues = ["Form aligned with reference"]

        frame_feedback.append(
            {
                "status": status_name,
                "joint_statuses": joint_statuses,
                "issues": issues,
                "posture_error": frame_error,
                "similarity": similarity_score,
            }
        )

    return {
        "similarity_score": similarity["score"],
        "label": label,
        "frame_wise_deviation": frame_deviation,
        "average_posture_error": round(average_posture_error, 2),
        "joint_angle_difference": round(_safe_nanmean(list(per_joint_error.values()), default=0.0), 2),
        "movement_smoothness": round(movement_smoothness, 2),
        "temporal_consistency": round(temporal_consistency, 2),
        "per_joint_error": {key: round(value, 2) for key, value in per_joint_error.items()},
        "feedback_messages": feedback_messages,
        "frame_feedback": frame_feedback,
        "aligned_length": aligned_length,
        "dtw_score": similarity["dtw_score"],
        "cosine_score": similarity["cosine_score"],
    }


def process_video(
    video_path,
    action_name,
    role_name,
    output_root,
    pose_extractor=None,
    feature_extractor=None,
    scorer=None,
    model_analyzer=None,
):
    pose_extractor = pose_extractor or PoseExtractor(debug=False)
    feature_extractor = feature_extractor or FeatureExtractor()
    scorer = scorer or ScoreCalculator()
    model_analyzer = model_analyzer or ModelPerformanceAnalyzer()

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    stem_name = Path(video_path).stem.replace(" ", "_")
    role_slug = role_name.lower().replace(" ", "_")

    pose_path = output_root / f"{role_slug}_{stem_name}_pose.npy"
    annotated_path = output_root / f"{role_slug}_{stem_name}_annotated.mp4"

    raw_landmarks, video_meta = pose_extractor._extract_raw_landmarks(video_path)
    smoothed_landmarks = pose_extractor._smooth_landmarks(raw_landmarks)
    angle_sequence = pose_extractor.compute_joint_angles(smoothed_landmarks)
    exercise_type = pose_extractor._exercise_type(action_name)

    signal_values = np.asarray(
        [pose_extractor._rep_signal(angles, exercise_type) for angles in angle_sequence],
        dtype=np.float32,
    )
    rep_count, rep_history, stage_history = pose_extractor._count_reps(signal_values, exercise_type)

    np.save(pose_path, smoothed_landmarks)

    feature_record = feature_extractor.extract_features(smoothed_landmarks, action_name)
    score_details = scorer.calculate_score(feature_record)
    prediction = model_analyzer.predict_action(feature_record)

    pose_extractor.annotate_video(
        video_path=video_path,
        output_path=str(annotated_path),
        landmarks=smoothed_landmarks,
        angle_sequence=angle_sequence,
        rep_history=rep_history,
        stage_history=stage_history,
        exercise_type=exercise_type,
        video_meta=video_meta,
        predicted_label=prediction["predicted_label"],
        prediction_confidence=prediction["confidence"],
    )

    return {
        "role": role_name,
        "action": action_name,
        "exercise_type": exercise_type,
        "video_path": str(video_path),
        "pose_path": str(pose_path),
        "annotated_video_path": str(annotated_path),
        "landmarks": smoothed_landmarks,
        "angle_sequence": angle_sequence,
        "feature_record": feature_record,
        "score_details": score_details,
        "prediction": prediction,
        "rep_count": int(rep_count),
        "rep_history": rep_history,
        "stage_history": stage_history,
        "video_meta": video_meta,
    }


def render_comparison_annotations(processed_video, comparison_result, output_path, pose_extractor=None):
    pose_extractor = pose_extractor or PoseExtractor(debug=False)
    pose_extractor.annotate_video(
        video_path=processed_video["video_path"],
        output_path=str(output_path),
        landmarks=processed_video["landmarks"],
        angle_sequence=processed_video["angle_sequence"],
        rep_history=processed_video["rep_history"],
        stage_history=processed_video["stage_history"],
        exercise_type=processed_video["exercise_type"],
        video_meta=processed_video["video_meta"],
        comparison_feedback=comparison_result.get("frame_feedback"),
        predicted_label=processed_video["prediction"]["predicted_label"],
        prediction_confidence=processed_video["prediction"]["confidence"],
    )
    return str(output_path)
