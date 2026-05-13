import '../models/pose_frame_model.dart';
import '../models/biomechanical_features.dart';
import '../core/utils/helpers.dart';
import '../core/constants/pose_constants.dart';
import '../core/constants/app_constants.dart';

class FeatureExtractionService {
  /// Extracts a 76-dimensional feature vector from the current pose and optional previous pose.
  static BiomechanicalFeatures extract(PoseFrameModel current, PoseFrameModel? previous) {
    final List<double> features = [];

    // 1. Joint Angles (12 features)
    final Map<String, double> currentAngles = {};
    PoseConstants.jointAngles.forEach((name, indices) {
      final angle = MathHelpers.calculateAngle(
        current.landmarks[indices[0]],
        current.landmarks[indices[1]],
        current.landmarks[indices[2]],
      );
      currentAngles[name] = angle;
      features.add(angle);
    });

    // 2. Angular Velocities (12 features)
    final double dt = previous != null 
        ? current.timestamp.difference(previous.timestamp).inMilliseconds / 1000.0 
        : 0.0;
    
    PoseConstants.jointAngles.forEach((name, indices) {
      if (previous == null || dt == 0) {
        features.add(0.0);
      } else {
        final prevAngle = MathHelpers.calculateAngle(
          previous.landmarks[indices[0]],
          previous.landmarks[indices[1]],
          previous.landmarks[indices[2]],
        );
        final velocity = (currentAngles[name]! - prevAngle) / dt;
        features.add(velocity);
      }
    });

    // 3. Landmark Positions (44 features: 22 landmarks * x,y)
    // We use indices 11 to 32 (Shoulders to Foot Index)
    for (int i = 11; i <= 32; i++) {
      features.add(current.landmarks[i].x);
      features.add(current.landmarks[i].y);
    }

    // 4. Symmetry Ratios (6 features: Left/Right ratio for 6 bilateral pairs)
    final bilateralPairs = [
      ['left_elbow', 'right_elbow'],
      ['left_shoulder', 'right_shoulder'],
      ['left_hip', 'right_hip'],
      ['left_knee', 'right_knee'],
      ['left_ankle', 'right_ankle'],
      ['left_trunk', 'right_trunk'],
    ];

    for (final pair in bilateralPairs) {
      final left = currentAngles[pair[0]]!;
      final right = currentAngles[pair[1]]!;
      // Ratio = (L - R) / (L + R + eps) normalized to [-1, 1]
      final symmetry = (left - right) / (left + right + 0.001);
      features.add(symmetry);
    }

    // 5. Center of Mass (COM) Displacement (2 features: x,y)
    // Approximation using the average of shoulders and hips
    final comX = (current.landmarks[11].x + current.landmarks[12].x + 
                  current.landmarks[23].x + current.landmarks[24].x) / 4.0;
    final comY = (current.landmarks[11].y + current.landmarks[12].y + 
                  current.landmarks[23].y + current.landmarks[24].y) / 4.0;
    features.add(comX);
    features.add(comY);

    // 6. Normalization (Z-Score)
    final normalizedFeatures = <double>[];
    for (int i = 0; i < features.length; i++) {
      final mean = AppConstants.featureMeans[i];
      final std = AppConstants.featureStds[i];
      normalizedFeatures.add((features[i] - mean) / (std + 0.00001));
    }

    return BiomechanicalFeatures(normalizedFeatures);
  }
}
