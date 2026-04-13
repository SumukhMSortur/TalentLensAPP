import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import pandas as pd


class FeatureExtractor:

    def __init__(self):
        pass

    # Calculate angle
    def calculate_angle(self, a, b, c):

        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(
            c[1] - b[1], c[0] - b[0]
        ) - np.arctan2(
            a[1] - b[1], a[0] - b[0]
        )

        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180:
            angle = 360 - angle

        return angle


    def extract_features(self, pose_data, action):

        features = []

        for frame in pose_data:

            kp = np.array(frame)

            # ---------------------
            # SQUAT FEATURES
            # ---------------------
            if "squat" in action.lower():

                left_knee = self.calculate_angle(
                    kp[23][:2], kp[25][:2], kp[27][:2]
                )

                right_knee = self.calculate_angle(
                    kp[24][:2], kp[26][:2], kp[28][:2]
                )

                back = self.calculate_angle(
                    kp[11][:2], kp[23][:2], kp[25][:2]
                )

                features.append([left_knee, right_knee, back])

            # ---------------------
            # PUSHUPS
            # ---------------------
            elif "push" in action.lower():

                left_arm = self.calculate_angle(
                    kp[11][:2], kp[13][:2], kp[15][:2]
                )

                right_arm = self.calculate_angle(
                    kp[12][:2], kp[14][:2], kp[16][:2]
                )

                back = self.calculate_angle(
                    kp[11][:2], kp[23][:2], kp[25][:2]
                )

                features.append([left_arm, right_arm, back])

            # ---------------------
            # PULLUPS
            # ---------------------
            elif "pull" in action.lower():

                left_arm = self.calculate_angle(
                    kp[11][:2], kp[13][:2], kp[15][:2]
                )

                right_arm = self.calculate_angle(
                    kp[12][:2], kp[14][:2], kp[16][:2]
                )

                shoulder = self.calculate_angle(
                    kp[13][:2], kp[11][:2], kp[23][:2]
                )

                features.append([left_arm, right_arm, shoulder])

        return np.array(features)


    def process_dataset(self, pose_path, save_path):

        os.makedirs(save_path, exist_ok=True)

        for action in os.listdir(pose_path):

            print(f"\nExtracting features: {action}")

            action_path = os.path.join(pose_path, action)
            save_action = os.path.join(save_path, action)

            os.makedirs(save_action, exist_ok=True)

            for file in tqdm(os.listdir(action_path)):

                pose_file = os.path.join(action_path, file)

                pose_data = np.load(pose_file)

                features = self.extract_features(pose_data, action)

                save_file = os.path.join(save_action, file)

                np.save(save_file, features)

                # Save CSV for demo
                csv_file = save_file.replace(".npy", ".csv")

                pd.DataFrame(features).to_csv(csv_file, index=False)

        print("Feature Extraction Completed")