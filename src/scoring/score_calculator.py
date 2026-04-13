import os
import numpy as np
import cv2
import random


class ScoreCalculator:

    def __init__(self):
        pass


    # -------------------------
    # SQUAT SCORING
    # -------------------------
    def squat_score(self, features):

        left_knee = features[:, 0]
        right_knee = features[:, 1]
        back = features[:, 2]

        depth_score = 100 - np.abs(np.mean(left_knee) - 90)
        symmetry_score = 100 - np.mean(np.abs(left_knee - right_knee))
        back_score = 100 - np.abs(np.mean(back) - 170)

        final = (
            0.4 * depth_score +
            0.3 * symmetry_score +
            0.3 * back_score
        )

        return max(0, min(100, final))


    # -------------------------
    # PUSHUP SCORING
    # -------------------------
    def pushup_score(self, features):

        left_arm = features[:, 0]
        right_arm = features[:, 1]
        back = features[:, 2]

        elbow_score = 100 - np.abs(np.mean(left_arm) - 90)
        symmetry_score = 100 - np.mean(np.abs(left_arm - right_arm))
        back_score = 100 - np.abs(np.mean(back) - 175)

        final = (
            0.4 * elbow_score +
            0.3 * symmetry_score +
            0.3 * back_score
        )

        return max(0, min(100, final))


    # -------------------------
    # PULLUP SCORING
    # -------------------------
    def pullup_score(self, features):

        left_arm = features[:, 0]
        right_arm = features[:, 1]
        shoulder = features[:, 2]

        contraction_score = 100 - np.mean(left_arm)
        symmetry_score = 100 - np.mean(np.abs(left_arm - right_arm))
        stability_score = 100 - np.std(shoulder)

        final = (
            0.4 * contraction_score +
            0.3 * symmetry_score +
            0.3 * stability_score
        )

        return max(0, min(100, final))


    # -------------------------
    # Video Player
    # -------------------------
    def play_video(self, video_path):

        print("Trying to play:", video_path)

        if not os.path.exists(video_path):
            print("Video not found:", video_path)
            return

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("Cannot open video:", video_path)
            return

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            cv2.imshow("Talent Lens AI Demo", frame)

            if cv2.waitKey(30) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


    # -------------------------
    # Find video automatically
    # -------------------------
    def find_video(self, folder, base_name):

        extensions = [".mp4", ".avi", ".mov"]

        for ext in extensions:

            video_path = os.path.join(folder, base_name + ext)

            if os.path.exists(video_path):
                return video_path

        return None


    # -------------------------
    # MAIN PROCESSING
    # -------------------------
    def process_dataset(self, feature_path):

        video_base = "outputs/pose_samples"

        actions = os.listdir(feature_path)

        action_files = {}

        for action in actions:

            action_path = os.path.join(feature_path, action)

            files = [
                f for f in os.listdir(action_path)
                if f.endswith(".npy")
            ]

            action_files[action] = random.sample(
                files, min(3, len(files))
            )

        for i in range(3):

            print("\n")
            print("=" * 60)
            print(f" ITERATION {i+1}")
            print("=" * 60)

            for action in actions:

                file = action_files[action][i]

                feature_file = os.path.join(
                    feature_path,
                    action,
                    file
                )

                features = np.load(feature_file)

                if "squat" in action.lower():
                    score = self.squat_score(features)

                elif "push" in action.lower():
                    score = self.pushup_score(features)

                elif "pull" in action.lower():
                    score = self.pullup_score(features)

                else:
                    score = 0

                base_name = file.replace(".npy", "")

                video_folder = os.path.join(
                    video_base,
                    action
                )

                video_file = self.find_video(
                    video_folder,
                    base_name
                )

                print("\n----------------------------------------")
                print(f"Action : {action}")
                print(f"Video  : {base_name}")
                print("----------------------------------------")

                if video_file:
                    self.play_video(video_file)
                else:
                    print("No video found for:", base_name)

                print("\nFINAL SCORE :", round(score, 2))
                print("----------------------------------------")