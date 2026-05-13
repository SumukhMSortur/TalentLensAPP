class CameraException implements Exception {
  final String message;
  final String? code;

  CameraException(this.message, [this.code]);

  @override
  String toString() => 'CameraException: [$code] $message';
}

class CameraPermissionException extends CameraException {
  CameraPermissionException(super.message, [super.code]);
}

class CameraInitializationException extends CameraException {
  CameraInitializationException(super.message, [super.code]);
}
