import 'dart:async';
import 'package:camera/camera.dart';
import '../core/constants/app_constants.dart';
import '../core/errors/exceptions.dart' as custom;

class CameraService {
  CameraController? _controller;
  final _frameStreamController = StreamController<CameraImage>.broadcast();
  int _frameCount = 0;

  CameraController? get controller => _controller;
  Stream<CameraImage> get frameStream => _frameStreamController.stream;

  Future<void> initialize() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw custom.CameraInitializationException('No cameras found on device');
      }

      // Use the back camera by default for better quality/stability
      final camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      _controller = CameraController(
        camera,
        ResolutionPreset.medium, // Balanced for performance (720p approx)
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420, // Native Android format
      );

      await _controller!.initialize();
    } on CameraException catch (e) {
      throw custom.CameraInitializationException(e.description ?? 'Unknown camera error', e.code);
    } catch (e) {
      throw custom.CameraInitializationException(e.toString());
    }
  }

  void startStream() {
    if (_controller == null || !_controller!.value.isInitialized) {
      throw custom.CameraInitializationException('Camera not initialized');
    }

    if (_controller!.value.isStreamingImages) return;

    _controller!.startImageStream((CameraImage image) {
      _frameCount++;
      
      // Throttling: only process every Nth frame to save CPU/Battery
      if (_frameCount % AppConstants.frameSkipRatio == 0) {
        if (!_frameStreamController.isClosed) {
          _frameStreamController.add(image);
        }
      }
    });
  }

  Future<void> stopStream() async {
    if (_controller != null && _controller!.value.isStreamingImages) {
      await _controller!.stopImageStream();
    }
  }

  void dispose() {
    stopStream();
    _controller?.dispose();
    _frameStreamController.close();
  }
}
