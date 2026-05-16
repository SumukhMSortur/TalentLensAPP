import 'package:camera/camera.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import '../models/keypoint_model.dart';
import '../models/pose_frame_model.dart';
import '../core/utils/image_utils.dart';

class PoseService {
  late final PoseDetector _poseDetector;
  int _frameIndex = 0;

  PoseService() {
    // Initialize with Base Pose Detection model (optimized for mobile)
    _poseDetector = PoseDetector(
      options: PoseDetectorOptions(
        mode: PoseDetectionMode.stream,
      ),
    );
  }

  Future<PoseFrameModel?> processFrame(CameraImage image, CameraDescription camera) async {
    final inputImage = ImageUtils.inputImageFromCameraImage(image, camera);
    if (inputImage == null) return null;

    try {
      final poses = await _poseDetector.processImage(inputImage);
      if (poses.isEmpty) return null;

      final pose = poses.first;
      final List<KeypointModel> landmarks = [];

      // MediaPipe standard 33 landmarks
      pose.landmarks.forEach((type, landmark) {
        landmarks.add(KeypointModel(
          index: type.index,
          // Normalize to [0, 1] based on input image dimensions
          x: landmark.x / image.width,
          y: landmark.y / image.height,
          z: landmark.z,
          visibility: landmark.likelihood,
        ));
      });

      // Ensure landmarks are sorted by index for consistent feature extraction
      landmarks.sort((a, b) => a.index.compareTo(b.index));

      return PoseFrameModel(
        landmarks: landmarks,
        timestamp: DateTime.now(),
        frameIndex: _frameIndex++,
      );
    } catch (e) {
      // In production, log this via the logger package
      return null;
    }
  }

  void dispose() {
    _poseDetector.close();
  }
}
