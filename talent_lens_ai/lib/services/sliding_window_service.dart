import 'dart:collection';
import 'dart:typed_data';
import '../models/biomechanical_features.dart';
import '../core/constants/app_constants.dart';

class SlidingWindowService {
  final int windowSize;
  final int featureDim;
  final Queue<BiomechanicalFeatures> _buffer = Queue();

  SlidingWindowService({
    this.windowSize = AppConstants.slidingWindowSize,
    this.featureDim = AppConstants.featureVectorDim,
  });

  /// Adds a new feature vector to the rolling buffer.
  void add(BiomechanicalFeatures features) {
    if (_buffer.length >= windowSize) {
      _buffer.removeFirst();
    }
    _buffer.add(features);
  }

  /// Returns the flattened tensor [1, 30, 76] for TFLite input.
  /// If the buffer is not full, it pads with zeros (cold-start handling).
  Float32List get tensor {
    final Float32List result = Float32List(windowSize * featureDim);
    
    int i = 0;
    // PADDING: if buffer is shorter than windowSize, the first (windowSize - buffer.length) 
    // slots remain 0.0 (default in Float32List).
    final int paddingCount = windowSize - _buffer.length;
    
    // FILLING: copy existing features into the end of the tensor
    for (final features in _buffer) {
      final int startOffset = (paddingCount + i) * featureDim;
      result.setRange(startOffset, startOffset + featureDim, features.vector);
      i++;
    }

    return result;
  }

  bool get isFull => _buffer.length >= windowSize;

  void clear() {
    _buffer.clear();
  }
}
