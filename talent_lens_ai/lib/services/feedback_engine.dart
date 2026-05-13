import '../models/feedback_model.dart';
import '../models/biomechanical_features.dart';
import '../core/constants/app_constants.dart';

class FeedbackEngine {
  /// Generates corrective feedback based on current biomechanical features.
  static List<FeedbackItem> generateFeedback(BiomechanicalFeatures features, double currentScore) {
    final List<FeedbackItem> feedback = [];

    // 1. General Score-based Feedback
    if (currentScore < AppConstants.scorePoorThreshold) {
      feedback.add(FeedbackItem(
        message: "Form needs improvement. Focus on controlled movement.",
        severity: FeedbackSeverity.critical,
        timestamp: DateTime.now(),
      ));
    } else if (currentScore > AppConstants.scoreGoodThreshold) {
      feedback.add(FeedbackItem(
        message: "Excellent form! Keep maintaining this consistency.",
        severity: FeedbackSeverity.good,
        timestamp: DateTime.now(),
      ));
    }

    // 2. Rule-based Biomechanical Feedback
    // Index Mapping (from FeatureExtractionService):
    // 0: left_elbow, 1: right_elbow, 2: left_shoulder, 3: right_shoulder, 
    // 4: left_hip, 5: right_hip, 6: left_knee, 7: right_knee, 
    // 8: left_ankle, 9: right_ankle, 10: left_trunk, 11: right_trunk

    // Example: Knee Over Toe / Depth check for Squats
    final leftKneeAngle = features.jointAngle(6);
    final rightKneeAngle = features.jointAngle(7);
    
    if (leftKneeAngle < 70 || rightKneeAngle < 70) {
      feedback.add(FeedbackItem(
        message: "Knees bending too far. Check your depth.",
        severity: FeedbackSeverity.warning,
        affectedJoint: "Knees",
        timestamp: DateTime.now(),
      ));
    }

    // Example: Symmetry Check
    // 12 Symmetry Ratios start at index 24 (wait, check FeatureExtractionService)
    // 0: angles, 12: velocities, 24: positions, 68: symmetry (6 ratios)
    // 12 + 12 + 44 = 68. Symmetry ratios start at index 68.
    
    final shoulderSymmetry = features.vector[69]; // left_shoulder/right_shoulder
    if (shoulderSymmetry.abs() > 0.15) {
      feedback.add(FeedbackItem(
        message: "Shoulders uneven. Balance your weight distribution.",
        severity: FeedbackSeverity.warning,
        affectedJoint: "Shoulders",
        timestamp: DateTime.now(),
      ));
    }

    return feedback;
  }
}
