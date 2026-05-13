class AppConstants {
  // App Info
  static const String appName = 'Talent Lens AI';
  static const String appVersion = '1.0.0';

  // Model Config
  static const String tfliteModelPath = 'models/aqanet_lstm.tflite';
  static const int slidingWindowSize = 30; // Number of frames in sequence
  static const int featureVectorDim = 76; // 12 angles + 12 velocities + 33x2 pos + sym + com

  // Camera Config
  static const int frameSkipRatio = 3; // Process every 3rd frame (targeting ~10 FPS processing)
  static const double minVisibilityThreshold = 0.5; // Landmarks below this are ignored

  // Feedback Thresholds
  static const double scorePoorThreshold = 40.0;
  static const double scoreGoodThreshold = 70.0;

  // Animation Durations
  static const int scoreAnimationMs = 150;
  static const int feedbackDismissMs = 3000;

  // Design Tokens
  static const double borderRadius = 16.0;
  static const double defaultPadding = 20.0;

  // Normalization Parameters (Z-Score)
  // These are placeholders - in a real app, these would be computed from the training dataset.
  static final List<double> featureMeans = List.filled(76, 0.0);
  static final List<double> featureStds = List.filled(76, 1.0);
}
