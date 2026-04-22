import json
import pickle
from pathlib import Path

import numpy as np


class ModelPerformanceAnalyzer:
    SUMMARY_KEYS = [
        "average_angle",
        "min_angle",
        "max_angle",
        "consistency_std",
        "symmetry_mean",
        "body_line_mean",
        "rep_depth_mean",
        "rep_top_mean",
        "rep_symmetry_mean",
        "rep_body_line_mean",
        "valid_frame_ratio",
    ]

    METRIC_FILE_CANDIDATES = (
        "metrics.json",
        "model_metrics.json",
        "training_metrics.json",
        "metrics.pkl",
        "model_metrics.pkl",
        "training_metrics.pkl",
    )

    def __init__(self, feature_root="dataset/features"):
        self.feature_root = Path(feature_root)

    @staticmethod
    def _safe_float(value, default=0.0):
        if value is None:
            return float(default)
        try:
            if np.isnan(value):
                return float(default)
        except TypeError:
            pass
        return float(value)

    def _load_feature_record(self, path_value):
        loaded = np.load(path_value, allow_pickle=True)
        if isinstance(loaded, np.ndarray) and loaded.dtype == object and loaded.shape == ():
            loaded = loaded.item()
        if not isinstance(loaded, dict):
            raise ValueError(f"Unsupported feature record in {path_value}")
        return loaded

    def _vectorize_summary(self, summary):
        vector = [self._safe_float(summary.get(key), default=0.0) for key in self.SUMMARY_KEYS]
        return np.asarray(vector, dtype=np.float32)

    def _dataset_records(self):
        records = []
        if not self.feature_root.exists():
            return records

        for action_dir in sorted(self.feature_root.iterdir()):
            if not action_dir.is_dir():
                continue

            for feature_file in sorted(action_dir.glob("*.npy")):
                try:
                    feature_record = self._load_feature_record(feature_file)
                except ValueError:
                    continue
                records.append(
                    {
                        "action": action_dir.name,
                        "path": str(feature_file),
                        "vector": self._vectorize_summary(feature_record.get("summary", {})),
                    }
                )
        return records

    @staticmethod
    def _softmax(logits):
        logits = np.asarray(logits, dtype=np.float32)
        logits = logits - np.max(logits)
        exps = np.exp(logits)
        denom = np.sum(exps)
        if denom <= 0:
            return np.full_like(exps, 1.0 / len(exps))
        return exps / denom

    def _find_saved_metrics_file(self):
        candidate_roots = [
            Path.cwd(),
            Path.cwd() / "outputs",
            Path.cwd() / "models",
            Path.cwd() / "artifacts",
        ]

        for root in candidate_roots:
            if not root.exists():
                continue
            for candidate_name in self.METRIC_FILE_CANDIDATES:
                candidate_path = root / candidate_name
                if candidate_path.exists():
                    return candidate_path
        return None

    def _load_saved_metrics(self):
        metrics_path = self._find_saved_metrics_file()
        if metrics_path is None:
            return None

        if metrics_path.suffix.lower() == ".json":
            data = json.loads(metrics_path.read_text(encoding="utf-8"))
        else:
            with open(metrics_path, "rb") as handle:
                data = pickle.load(handle)

        if not isinstance(data, dict):
            return None

        return {
            "source": f"saved metrics: {metrics_path.name}",
            "accuracy": data.get("accuracy"),
            "loss": data.get("loss"),
            "prediction_confidence": data.get("prediction_confidence"),
            "confusion_matrix": data.get("confusion_matrix"),
            "labels": data.get("labels"),
        }

    def _baseline_metrics(self):
        records = self._dataset_records()
        if len(records) < 3:
            return {
                "source": "fallback baseline",
                "accuracy": None,
                "loss": None,
                "prediction_confidence": None,
                "confusion_matrix": None,
                "labels": None,
            }

        labels = sorted({record["action"] for record in records})
        label_to_index = {label: index for index, label in enumerate(labels)}
        confusion = np.zeros((len(labels), len(labels)), dtype=np.int32)
        correct = 0
        loss_values = []
        confidence_values = []

        for sample_index, sample in enumerate(records):
            centroids = {}
            for label in labels:
                vectors = [
                    record["vector"]
                    for index, record in enumerate(records)
                    if record["action"] == label and index != sample_index
                ]
                if vectors:
                    centroids[label] = np.mean(vectors, axis=0)

            if not centroids:
                continue

            distance_items = []
            for label, centroid in centroids.items():
                distance = float(np.linalg.norm(sample["vector"] - centroid))
                distance_items.append((label, distance))

            ordered = sorted(distance_items, key=lambda item: item[1])
            predicted_label = ordered[0][0]
            confidence_scores = self._softmax([-item[1] for item in ordered])
            confidence_lookup = {
                label: float(confidence_scores[index])
                for index, (label, _) in enumerate(ordered)
            }

            true_index = label_to_index[sample["action"]]
            pred_index = label_to_index[predicted_label]
            confusion[true_index, pred_index] += 1

            if predicted_label == sample["action"]:
                correct += 1

            true_confidence = max(confidence_lookup.get(sample["action"], 1e-8), 1e-8)
            loss_values.append(float(-np.log(true_confidence)))
            confidence_values.append(float(confidence_lookup.get(predicted_label, 0.0)))

        sample_count = max(len(records), 1)
        accuracy = correct / sample_count
        loss = float(np.mean(loss_values)) if loss_values else None
        confidence = float(np.mean(confidence_values)) if confidence_values else None

        return {
            "source": "fallback nearest-centroid baseline",
            "accuracy": accuracy,
            "loss": loss,
            "prediction_confidence": confidence,
            "confusion_matrix": confusion.tolist(),
            "labels": labels,
        }

    def load_metrics(self):
        return self._load_saved_metrics() or self._baseline_metrics()

    def predict_action(self, feature_record):
        records = self._dataset_records()
        if not records:
            action_name = feature_record.get("action", "unknown")
            return {
                "predicted_label": action_name,
                "confidence": 0.0,
                "probabilities": {action_name: 1.0},
            }

        vector = self._vectorize_summary(feature_record.get("summary", {}))
        labels = sorted({record["action"] for record in records})
        centroids = {
            label: np.mean(
                [record["vector"] for record in records if record["action"] == label],
                axis=0,
            )
            for label in labels
        }

        ordered = sorted(
            ((label, float(np.linalg.norm(vector - centroid))) for label, centroid in centroids.items()),
            key=lambda item: item[1],
        )
        probabilities = self._softmax([-item[1] for item in ordered])
        probability_map = {
            label: float(probabilities[index])
            for index, (label, _) in enumerate(ordered)
        }
        predicted_label = ordered[0][0]
        return {
            "predicted_label": predicted_label,
            "confidence": float(probability_map[predicted_label]),
            "probabilities": probability_map,
        }
