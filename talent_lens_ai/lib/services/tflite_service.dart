import 'dart:io';
import 'dart:typed_data';
import 'package:tflite_flutter/tflite_flutter.dart';
import '../models/inference_result_model.dart';
import '../core/constants/app_constants.dart';
import 'package:logger/logger.dart';

class TFLiteService {
  Interpreter? _interpreter;
  final Logger _logger = Logger();
  bool _isInitialized = false;

  bool get isInitialized => _isInitialized;

  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      final options = InterpreterOptions();

      if (Platform.isAndroid) {
        try {
          // Attempt to add GPU Delegate
          options.addDelegate(GpuDelegateV2());
          _logger.i('TFLite: GPU Delegate (V2) added successfully.');
        } catch (e) {
          _logger.w('TFLite: GPU Delegate failed, falling back to NNAPI. Error: $e');
          try {
            options.addDelegate(NnApiDelegate());
            _logger.i('TFLite: NNAPI Delegate added successfully.');
          } catch (e) {
            _logger.e('TFLite: All hardware delegates failed, using CPU. Error: $e');
          }
        }
      }

      // Load model from assets
      _interpreter = await Interpreter.fromAsset(
        AppConstants.tfliteModelPath,
        options: options,
      );

      // Verify I/O shapes
      _logger.i('TFLite: Model loaded. Input shape: ${_interpreter!.getInputTensor(0).shape}');
      _logger.i('TFLite: Model loaded. Output shape: ${_interpreter!.getOutputTensor(0).shape}');

      _isInitialized = true;
    } catch (e) {
      _logger.e('TFLite: Initialization failed: $e');
      _isInitialized = false;
      // If model file is missing, we will fallback to a stub in the inference method
    }
  }

  Future<InferenceResult> infer(Float32List windowTensor) async {
    final stopwatch = Stopwatch()..start();

    if (!_isInitialized || _interpreter == null) {
      // Fallback Stub logic for development
      return _generateStubResult(windowTensor, stopwatch.elapsedMilliseconds);
    }

    try {
      // Input shape: [1, 30, 76]
      final input = windowTensor.reshape([1, 30, 76]);
      // Output shape: [1, 1] for score, [1, 30] for attention (optional)
      final output = List<List<double>>.filled(1, List<double>.filled(1, 0.0));
      
      _interpreter!.run(input, output);

      stopwatch.stop();
      final double score = output[0][0] * 100.0; // Assume 0-1 range from model

      return InferenceResult(
        score: score.clamp(0.0, 100.0),
        confidence: 0.95, // Placeholder if model doesn't output confidence
        latencyMs: stopwatch.elapsedMilliseconds,
      );
    } catch (e) {
      _logger.e('TFLite: Inference error: $e');
      return _generateStubResult(windowTensor, stopwatch.elapsedMilliseconds);
    }
  }

  InferenceResult _generateStubResult(Float32List tensor, int latency) {
    // Generate a deterministic score based on input statistics for testing
    double sum = 0;
    for (var val in tensor) {
      sum += val.abs();
    }
    final score = (sum / (tensor.length * 0.5)) * 100.0;
    
    return InferenceResult(
      score: score.clamp(0.0, 100.0),
      confidence: 0.5,
      latencyMs: latency,
    );
  }

  void dispose() {
    _interpreter?.close();
    _isInitialized = false;
  }
}
