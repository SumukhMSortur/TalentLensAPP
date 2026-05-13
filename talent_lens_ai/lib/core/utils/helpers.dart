import 'dart:math';
import '../constants/pose_constants.dart';
import '../../models/keypoint_model.dart';

class MathHelpers {
  /// Computes the angle (in degrees) at joint B formed by points A, B, and C.
  /// Uses atan2 for numerical stability.
  static double calculateAngle(KeypointModel a, KeypointModel b, KeypointModel c) {
    // Vectors BA and BC
    final double baX = a.x - b.x;
    final double baY = a.y - b.y;
    final double bcX = c.x - b.x;
    final double bcY = c.y - b.y;

    // Dot product and magnitudes
    final double dotProduct = (baX * bcX) + (baY * bcY);
    final double magBA = sqrt(baX * baX + baY * baY);
    final double magBC = sqrt(bcX * bcX + bcY * bcY);

    if (magBA == 0 || magBC == 0) return 0.0;

    // Cosine of the angle
    double cosTheta = dotProduct / (magBA * magBC);
    // Clamp for precision errors
    cosTheta = cosTheta.clamp(-1.0, 1.0);

    // Angle in radians
    final double angleRad = acos(cosTheta);
    // Convert to degrees
    return angleRad * (180.0 / pi);
  }

  /// Computes the Euclidean distance between two points.
  static double distance(KeypointModel a, KeypointModel b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));
  }

  /// Computes the midpoint between two points.
  static List<double> midpoint(KeypointModel a, KeypointModel b) {
    return [(a.x + b.x) / 2, (a.y + b.y) / 2];
  }
}
