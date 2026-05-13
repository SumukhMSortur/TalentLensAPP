import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/camera_service.dart';
import 'package:camera/camera.dart';

enum CameraStatus { initial, initializing, streaming, error }

class CameraState {
  final CameraStatus status;
  final String? errorMessage;
  final CameraController? controller;

  CameraState({
    required this.status,
    this.errorMessage,
    this.controller,
  });

  factory CameraState.initial() => CameraState(status: CameraStatus.initial);

  CameraState copyWith({
    CameraStatus? status,
    String? errorMessage,
    CameraController? controller,
  }) {
    return CameraState(
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
      controller: controller ?? this.controller,
    );
  }
}

final cameraServiceProvider = Provider.autoDispose<CameraService>((ref) {
  final service = CameraService();
  ref.onDispose(() => service.dispose());
  return service;
});

class CameraNotifier extends StateNotifier<CameraState> {
  final CameraService _cameraService;

  CameraNotifier(this._cameraService) : super(CameraState.initial());

  Future<void> initialize() async {
    state = state.copyWith(status: CameraStatus.initializing);
    try {
      await _cameraService.initialize();
      _cameraService.startStream();
      state = state.copyWith(
        status: CameraStatus.streaming,
        controller: _cameraService.controller,
      );
    } catch (e) {
      state = state.copyWith(
        status: CameraStatus.error,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> toggleStream() async {
    if (state.status == CameraStatus.streaming) {
      await _cameraService.stopStream();
      state = state.copyWith(status: CameraStatus.initial);
    } else {
      _cameraService.startStream();
      state = state.copyWith(status: CameraStatus.streaming);
    }
  }
}

final cameraProvider = StateNotifierProvider.autoDispose<CameraNotifier, CameraState>((ref) {
  final service = ref.watch(cameraServiceProvider);
  return CameraNotifier(service);
});

final cameraFrameStreamProvider = StreamProvider.autoDispose<CameraImage>((ref) {
  final service = ref.watch(cameraServiceProvider);
  return service.frameStream;
});
