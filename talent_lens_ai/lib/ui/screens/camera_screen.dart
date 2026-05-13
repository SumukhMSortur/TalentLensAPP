import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import '../../providers/camera_provider.dart';
import '../../providers/pose_provider.dart';
import '../../providers/inference_provider.dart';
import '../../ui/theme/app_colors.dart';
import '../../widgets/skeleton_overlay.dart';
import '../../widgets/score_card.dart';
import '../../widgets/feedback_widget.dart';

class CameraScreen extends ConsumerStatefulWidget {
  const CameraScreen({super.key});

  @override
  ConsumerState<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends ConsumerState<CameraScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(cameraProvider.notifier).initialize());
  }

  @override
  Widget build(BuildContext context) {
    final cameraState = ref.watch(cameraProvider);
    final poseFrame = ref.watch(poseFrameProvider).value;
    final inferenceState = ref.watch(inferenceProvider).value;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 1. Camera Preview
          _buildCameraPreview(cameraState),

          // 2. Skeleton Overlay
          if (cameraState.status == CameraStatus.streaming && poseFrame != null)
            Positioned.fill(
              child: CustomPaint(
                painter: SkeletonOverlay(
                  pose: poseFrame,
                  imageSize: cameraState.controller!.value.previewSize!,
                ),
              ),
            ),

          // 3. UI Overlays (Scores, Controls, Feedback)
          _buildTopBar(context),
          
          if (inferenceState?.result != null)
            Positioned(
              top: 100,
              right: 20,
              child: ScoreCard(score: inferenceState!.result!.score),
            ),

          if (inferenceState?.feedback != null)
            Positioned(
              bottom: 40,
              left: 0,
              right: 0,
              child: FeedbackWidget(feedbackItems: inferenceState!.feedback),
            ),

          if (cameraState.status == CameraStatus.initializing)
            const Center(
              child: CircularProgressIndicator(color: AppColors.accent),
            ),

          if (cameraState.status == CameraStatus.error)
            _buildErrorState(cameraState.errorMessage),
        ],
      ),
    );
  }

  Widget _buildTopBar(BuildContext context) {
    return Positioned(
      top: 40,
      left: 0,
      right: 0,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.close, color: Colors.white, size: 28),
              onPressed: () => Navigator.pop(context),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.5),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.accent.withOpacity(0.5)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.circle, color: Colors.red, size: 10),
                  const SizedBox(width: 8),
                  Text(
                    'LIVE ANALYSIS',
                    style: TextStyle(
                      fontFamily: 'Rajdhani',
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.accent,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 48), // Spacer for symmetry
          ],
        ),
      ),
    );
  }

  Widget _buildCameraPreview(CameraState state) {
    if (state.status != CameraStatus.streaming || state.controller == null) {
      return Container(color: Colors.black);
    }

    final size = MediaQuery.of(context).size;
    var scale = size.aspectRatio * state.controller!.value.aspectRatio;
    if (scale < 1) scale = 1 / scale;

    return Transform.scale(
      scale: scale,
      child: Center(
        child: CameraPreview(state.controller!),
      ),
    );
  }

  Widget _buildErrorState(String? message) {
    return Container(
      color: AppColors.background.withOpacity(0.9),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: AppColors.error, size: 64),
              const SizedBox(height: 16),
              Text(
                'CAMERA ERROR',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: AppColors.error),
              ),
              const SizedBox(height: 8),
              Text(
                message ?? 'Unknown error occurred while accessing camera',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => ref.read(cameraProvider.notifier).initialize(),
                child: const Text('RETRY'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
