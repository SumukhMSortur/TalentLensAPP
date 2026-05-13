import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/pose_service.dart';
import '../models/pose_frame_model.dart';
import 'camera_provider.dart';

final poseServiceProvider = Provider.autoDispose<PoseService>((ref) {
  final service = PoseService();
  ref.onDispose(() => service.dispose());
  return service;
});

final poseFrameProvider = StreamProvider.autoDispose<PoseFrameModel?>((ref) {
  final poseService = ref.watch(poseServiceProvider);
  final cameraState = ref.watch(cameraProvider);
  final frameStream = ref.watch(cameraFrameStreamProvider);

  // If camera isn't streaming or controller isn't ready, don't process
  if (cameraState.status != CameraStatus.streaming || cameraState.controller == null) {
    return Stream.value(null);
  }

  final cameraDescription = cameraState.controller!.description;

  return frameStream.when(
    data: (image) async* {
      final poseFrame = await poseService.processFrame(image, cameraDescription);
      yield poseFrame;
    },
    loading: () => Stream.value(null),
    error: (err, stack) => Stream.value(null),
  );
});
