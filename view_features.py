import os
import argparse
import sys

import matplotlib
import numpy as np


if "--save" in sys.argv:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize saved feature metrics for one processed clip.",
    )
    parser.add_argument(
        "--class-name",
        default="squat",
        help="Action folder inside dataset/features. Defaults to squat.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Specific .npy feature file to visualize. Defaults to the first file in the folder.",
    )
    parser.add_argument(
        "--save",
        default=None,
        help="Optional output path for a PNG plot. If omitted, the script tries to open an interactive window.",
    )
    return parser.parse_args()


def load_feature_record(feature_path):
    loaded = np.load(feature_path, allow_pickle=True)

    if isinstance(loaded, np.ndarray) and loaded.dtype == object and loaded.shape == ():
        loaded = loaded.item()

    if not isinstance(loaded, dict) or "frame_metrics" not in loaded:
        raise ValueError(f"Unsupported feature format in {feature_path}")

    return loaded


def main():
    args = parse_args()
    feature_folder = os.path.join("dataset", "features", args.class_name)

    if not os.path.isdir(feature_folder):
        raise FileNotFoundError(f"Feature folder not found: {feature_folder}")

    if args.file:
        feature_path = os.path.join(feature_folder, args.file)
    else:
        npy_files = sorted(
            file_name for file_name in os.listdir(feature_folder) if file_name.lower().endswith(".npy")
        )
        if not npy_files:
            raise FileNotFoundError(f"No .npy feature files found in {feature_folder}")
        feature_path = os.path.join(feature_folder, npy_files[0])

    record = load_feature_record(feature_path)
    metrics = record["frame_metrics"]

    print(f"Feature file: {feature_path}")
    print(f"Exercise type: {record.get('exercise_type')}")
    print(f"Frame count: {record.get('frame_count')}")
    print(f"Rep count: {record.get('rep_count')}")
    print(f"Available metrics: {', '.join(sorted(metrics.keys()))}")
    print("\nSummary:")
    for key, value in sorted(record.get("summary", {}).items()):
        print(f"- {key}: {value}")

    plt.figure(figsize=(10, 5))

    if "left_knee_angle" in metrics:
        plt.plot(metrics["left_knee_angle"], label="Left Knee Angle")
    if "right_knee_angle" in metrics:
        plt.plot(metrics["right_knee_angle"], label="Right Knee Angle")
    if "left_elbow_angle" in metrics:
        plt.plot(metrics["left_elbow_angle"], label="Left Elbow Angle")
    if "right_elbow_angle" in metrics:
        plt.plot(metrics["right_elbow_angle"], label="Right Elbow Angle")
    if "primary_angle" in metrics:
        plt.plot(metrics["primary_angle"], label="Primary Angle", linewidth=2)

    plt.legend()
    plt.title(f"Feature Visualization: {os.path.basename(feature_path)}")
    plt.xlabel("Frame")
    plt.ylabel("Angle")
    plt.tight_layout()

    output_path = args.save
    try:
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            plt.savefig(output_path, dpi=150)
            print(f"Plot saved to {output_path}")
        else:
            plt.show()
    except Exception as exc:
        fallback_dir = os.path.join("outputs", "feature_plots")
        os.makedirs(fallback_dir, exist_ok=True)
        fallback_path = os.path.join(
            fallback_dir,
            os.path.splitext(os.path.basename(feature_path))[0] + ".png",
        )
        plt.savefig(fallback_path, dpi=150)
        print(f"Interactive plot unavailable ({exc}).")
        print(f"Plot saved to {fallback_path}")


if __name__ == "__main__":
    main()
