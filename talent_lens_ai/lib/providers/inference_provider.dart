import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/tflite_service.dart';
import '../services/sliding_window_service.dart';
import '../services/feature_extraction_service.dart';
import '../services/feedback_engine.dart';
import '../models/inference_result_model.dart';
import '../models/feedback_model.dart';
import '../models/pose_frame_model.dart';
import 'pose_provider.dart';

/**
 * PROVIDER DEPENDENCY GRAPH
 * 
 * [SettingsProvider] ────┐
 *                        ▼
 * [CameraProvider] ──► [PoseProvider] ──► [InferenceProvider] ──► [SessionProvider]
 *                        ▲                  ▲
 * [CameraService] ───────┘                  │
 *                                           ▼
 * [TFLiteService] ──────────────────► [FeedbackEngine]
 */

// Permanent singleton — must NOT be autoDispose.
// If autoDispose, the provider is destroyed and recreated on every stream
// rebuild (once per camera frame), causing TFLite to re-initialize in an
// infinite loop and flooding the log with "not a valid Flatbuffer" errors.
final tfliteServiceProvider = Provider<TFLiteService>((ref) {
  final service = TFLiteService();
  service.initialize(); // called exactly once for the app's lifetime
  ref.onDispose(() => service.dispose());
  return service;
});

// Also permanent — must retain the rolling 30-frame buffer across rebuilds.
final slidingWindowProvider = Provider<SlidingWindowService>((ref) {
  return SlidingWindowService();
});

class InferenceState {
  final InferenceResult? result;
  final List<FeedbackItem> feedback;
  final bool isModelLoaded;

  InferenceState({
    this.result,
    this.feedback = const [],
    this.isModelLoaded = false,
  });

  InferenceState copyWith({
    InferenceResult? result,
    List<FeedbackItem>? feedback,
    bool? isModelLoaded,
  }) {
    return InferenceState(
      result: result ?? this.result,
      feedback: feedback ?? this.feedback,
      isModelLoaded: isModelLoaded ?? this.isModelLoaded,
    );
  }
}

final inferenceProvider = StreamProvider.autoDispose<InferenceState>((ref) async* {
  final tfliteService = ref.watch(tfliteServiceProvider);
  final slidingWindow = ref.watch(slidingWindowProvider);
  final poseFrameAsync = ref.watch(poseFrameProvider);

  PoseFrameModel? previousFrame;
  InferenceState currentState = InferenceState(isModelLoaded: tfliteService.isInitialized);

  yield* poseFrameAsync.when(
    data: (currentFrame) async* {
      if (currentFrame == null) {
        yield currentState;
        return;
      }

      // 1. Feature Extraction
      final features = FeatureExtractionService.extract(currentFrame, previousFrame);
      previousFrame = currentFrame;

      // 2. Sliding Window update
      slidingWindow.add(features);

      // 3. TFLite Inference
      final result = await tfliteService.infer(slidingWindow.tensor);

      // 4. Feedback Generation
      final feedback = FeedbackEngine.generateFeedback(features, result.score);

      currentState = currentState.copyWith(
        result: result,
        feedback: feedback,
        isModelLoaded: tfliteService.isInitialized,
      );

      yield currentState;
    },
    loading: () => Stream.value(currentState),
    error: (err, stack) => Stream.value(currentState),
  );
});
