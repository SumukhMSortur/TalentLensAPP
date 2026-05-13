class PoseConstants {
  // MediaPipe Pose Landmark Indices (33 points)
  static const int nose = 0;
  static const int leftEyeInner = 1;
  static const int leftEye = 2;
  static const int leftEyeOuter = 3;
  static const int rightEyeInner = 4;
  static const int rightEye = 5;
  static const int rightEyeOuter = 6;
  static const int leftEar = 7;
  static const int rightEar = 8;
  static const int mouthLeft = 9;
  static const int mouthRight = 10;
  static const int leftShoulder = 11;
  static const int rightShoulder = 12;
  static const int leftElbow = 13;
  static const int rightElbow = 14;
  static const int leftWrist = 15;
  static const int rightWrist = 16;
  static const int leftPinky = 17;
  static const int rightPinky = 18;
  static const int leftIndex = 19;
  static const int rightIndex = 20;
  static const int leftThumb = 21;
  static const int rightThumb = 22;
  static const int leftHip = 23;
  static const int rightHip = 24;
  static const int leftKnee = 25;
  static const int rightKnee = 26;
  static const int leftAnkle = 27;
  static const int rightAnkle = 28;
  static const int leftHeel = 29;
  static const int rightHeel = 30;
  static const int leftFootIndex = 31;
  static const int rightFootIndex = 32;

  // Connection Pairs for Drawing (35 pairs)
  static const List<List<int>> connections = [
    [nose, leftEyeInner], [leftEyeInner, leftEye], [leftEye, leftEyeOuter], [leftEyeOuter, leftEar],
    [nose, rightEyeInner], [rightEyeInner, rightEye], [rightEye, rightEyeOuter], [rightEyeOuter, rightEar],
    [mouthLeft, mouthRight],
    [leftShoulder, rightShoulder],
    [leftShoulder, leftElbow], [leftElbow, leftWrist],
    [rightShoulder, rightElbow], [rightElbow, rightWrist],
    [leftShoulder, leftHip], [rightShoulder, rightHip], [leftHip, rightHip],
    [leftHip, leftKnee], [leftKnee, leftAnkle],
    [rightHip, rightKnee], [rightKnee, rightAnkle],
    [leftAnkle, leftHeel], [leftAnkle, leftFootIndex], [leftHeel, leftFootIndex],
    [rightAnkle, rightHeel], [rightAnkle, rightFootIndex], [rightHeel, rightFootIndex],
    [leftWrist, leftPinky], [leftWrist, leftIndex], [leftWrist, leftThumb],
    [rightWrist, rightPinky], [rightWrist, rightIndex], [rightWrist, rightThumb],
  ];

  // Joint Angle Definitions (12 bilateral joints)
  static const Map<String, List<int>> jointAngles = {
    'left_elbow': [leftShoulder, leftElbow, leftWrist],
    'right_elbow': [rightShoulder, rightElbow, rightWrist],
    'left_shoulder': [leftHip, leftShoulder, leftElbow],
    'right_shoulder': [rightHip, rightShoulder, rightElbow],
    'left_hip': [leftShoulder, leftHip, leftKnee],
    'right_hip': [rightShoulder, rightHip, rightKnee],
    'left_knee': [leftHip, leftKnee, leftAnkle],
    'right_knee': [rightHip, rightKnee, rightAnkle],
    'left_ankle': [leftKnee, leftAnkle, leftFootIndex],
    'right_ankle': [rightKnee, rightAnkle, rightFootIndex],
    // Torso/Stability angles
    'left_trunk': [leftShoulder, leftHip, leftAnkle],
    'right_trunk': [rightShoulder, rightHip, rightAnkle],
  };
}
