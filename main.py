import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.pose.pose_extractor import PoseExtractor
from src.features.feature_extractor import FeatureExtractor
from src.scoring.score_calculator import ScoreCalculator


def main():

    dataset_path = "dataset/videos"
    pose_path = "dataset/poses"
    feature_path = "dataset/features"

    # Always run pose extraction
    print("\nRunning Pose Extraction...")

    pose_extractor = PoseExtractor()
    pose_extractor.extract_dataset(
        dataset_path,
        pose_path
    )

    # Feature Extraction
    print("\nRunning Feature Extraction...")

    feature_extractor = FeatureExtractor()
    feature_extractor.process_dataset(
        pose_path,
        feature_path
    )

    # Scoring
    print("\nRunning Scoring...")

    scorer = ScoreCalculator()
    scorer.process_dataset(feature_path)


if __name__ == "__main__":
    main()