import 'dart:math';
import 'dart:typed_data';

class DataProcessing {
  /// Applies a simple moving average to smooth noisy signal data.
  static List<double> movingAverage(List<double> data, int window) {
    if (data.length < window) return data;
    final List<double> result = [];
    for (int i = 0; i <= data.length - window; i++) {
      double sum = 0;
      for (int j = 0; j < window; j++) {
        sum += data[i + j];
      }
      result.add(sum / window);
    }
    return result;
  }

  /// Clamps values between a min and max.
  static double clamp(double value, double min, double max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
  }

  /// Normalizes a score from [0, 1] to [0, 100].
  static double normalizeScore(double rawScore) {
    return (rawScore * 100.0).clamp(0.0, 100.0);
  }
}
