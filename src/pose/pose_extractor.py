import os
import cv2
import numpy as np
import random
from tqdm import tqdm
import mediapipe as mp


class PoseExtractor:

    def __init__(self):

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )


    # -----------------------------
    # Angle Calculation
    # -----------------------------
    def calculate_angle(self, a, b, c):

        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(
            c[1]-b[1], c[0]-b[0]
        ) - np.arctan2(
            a[1]-b[1], a[0]-b[0]
        )

        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180:
            angle = 360-angle

        return angle


    # -----------------------------
    # Score Function
    # -----------------------------
    def calculate_score(self, angle, ideal):

        score = 100 - abs(angle - ideal)

        return max(0, min(100, score))


    # -----------------------------
    # Extract Pose
    # -----------------------------
    def extract_pose(self, video_path, save_video_path, action):

        cap = cv2.VideoCapture(video_path)

        pose_sequence = []

        width = int(cap.get(3))
        height = int(cap.get(4))
        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps == 0:
            fps = 20

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        out = cv2.VideoWriter(
            save_video_path,
            fourcc,
            fps,
            (width, height)
        )

        while cap.isOpened():

            ret, frame = cap.read()

            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = self.pose.process(image)

            if results.pose_landmarks:

                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )

                h, w, _ = frame.shape

                keypoints = []

                for lm in results.pose_landmarks.landmark:
                    keypoints.append([lm.x*w, lm.y*h, lm.visibility])

                kp = np.array(keypoints)

                # -----------------------------
                # Angles
                # -----------------------------

                left_arm = self.calculate_angle(
                    kp[11][:2], kp[13][:2], kp[15][:2]
                )

                right_arm = self.calculate_angle(
                    kp[12][:2], kp[14][:2], kp[16][:2]
                )

                left_knee = self.calculate_angle(
                    kp[23][:2], kp[25][:2], kp[27][:2]
                )

                right_knee = self.calculate_angle(
                    kp[24][:2], kp[26][:2], kp[28][:2]
                )

                # -----------------------------
                # Scores
                # -----------------------------

                left_arm_score = self.calculate_score(left_arm, 90)
                right_arm_score = self.calculate_score(right_arm, 90)

                left_knee_score = self.calculate_score(left_knee, 90)
                right_knee_score = self.calculate_score(right_knee, 90)


                # -----------------------------
                # Draw Angles + Score
                # -----------------------------

                def draw(frame, angle, score, point, color):

                    x = int(point[0])
                    y = int(point[1])

                    cv2.putText(
                        frame,
                        f"{int(angle)}",
                        (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )

                    cv2.putText(
                        frame,
                        f"S:{int(score)}",
                        (x, y+20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )


                # Arms
                draw(frame, left_arm, left_arm_score, kp[13][:2], (0,255,0))
                draw(frame, right_arm, right_arm_score, kp[14][:2], (0,255,0))

                # Knees
                draw(frame, left_knee, left_knee_score, kp[25][:2], (255,0,0))
                draw(frame, right_knee, right_knee_score, kp[26][:2], (255,0,0))


                pose_sequence.append([
                    left_arm,
                    right_arm,
                    left_knee,
                    right_knee
                ])

            out.write(frame)

        cap.release()
        out.release()

        return np.array(pose_sequence)


    # -----------------------------
    # Extract Dataset
    # -----------------------------
    def extract_dataset(self, dataset_path, save_path):

        os.makedirs(save_path, exist_ok=True)

        pose_video_base = "outputs/pose_samples"
        os.makedirs(pose_video_base, exist_ok=True)

        for action in os.listdir(dataset_path):

            print(f"\nProcessing {action}...")

            action_path = os.path.join(dataset_path, action)

            save_action_path = os.path.join(save_path, action)
            pose_video_action = os.path.join(pose_video_base, action)

            os.makedirs(save_action_path, exist_ok=True)
            os.makedirs(pose_video_action, exist_ok=True)

            videos = os.listdir(action_path)

            if len(videos) > 3:
                videos = random.sample(videos, 3)

            for video in tqdm(videos):

                video_path = os.path.join(action_path, video)

                pose_video_path = os.path.join(
                    pose_video_action,
                    video.split('.')[0] + ".mp4"
                )

                pose_sequence = self.extract_pose(
                    video_path,
                    pose_video_path,
                    action
                )

                save_file = os.path.join(
                    save_action_path,
                    video.split('.')[0] + ".npy"
                )

                np.save(save_file, pose_sequence)

        print("\nPose Extraction Completed")