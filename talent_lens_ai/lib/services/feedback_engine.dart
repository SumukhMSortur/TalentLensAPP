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

    // NOTE: After Z-score normalisation the angles are dimensionless.
    // We only use raw-index accessors for symmetry ratios (indices 68-73)
    // which are already ratio-based and unaffected by normalisation.

    // Example: Symmetry Check
    // Layout: 12 angles | 12 velocities | 44 positions | 6 symmetry | 2 COM
    //         [0-11]      [12-23]          [24-67]        [68-73]     [74-75]
    // Pair order: elbow(68), shoulder(69), hip(70), knee(71), ankle(72), trunk(73)
    if (features.vector.length > 69) {
      final shoulderSymmetry = features.vector[69]; // shoulder L/R ratio
      if (shoulderSymmetry.abs() > 0.15) {
        feedback.add(FeedbackItem(
          message: "Shoulders uneven. Balance your weight distribution.",
          severity: FeedbackSeverity.warning,
          affectedJoint: "Shoulders",
          timestamp: DateTime.now(),
        ));
      }
    }

    return feedback;
  }
}
