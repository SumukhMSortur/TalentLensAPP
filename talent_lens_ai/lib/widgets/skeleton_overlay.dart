import 'package:flutter/material.dart';
import '../models/pose_frame_model.dart';
import '../core/constants/pose_constants.dart';
import '../ui/theme/app_colors.dart';

class SkeletonOverlay extends CustomPainter {
  final PoseFrameModel? pose;
  final Size imageSize;

  SkeletonOverlay({
    required this.pose,
    required this.imageSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (pose == null) return;

    final paintCircle = Paint()
      ..style = PaintingStyle.fill
      ..strokeWidth = 2.0;

    final paintLine = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round;

    // 1. Draw Connections (Bones)
    for (final connection in PoseConstants.connections) {
      final int idx0 = connection[0];
      final int idx1 = connection[1];
      // Guard: only draw if both landmark indices are within bounds
      if (idx0 >= pose!.landmarks.length || idx1 >= pose!.landmarks.length) continue;
      final startNode = pose!.landmarks[idx0];
      final endNode = pose!.landmarks[idx1];

      // Only draw if both points have decent visibility
      if (startNode.visibility > 0.5 && endNode.visibility > 0.5) {
        final start = _mapOffset(startNode.x, startNode.y, size);
        final end = _mapOffset(endNode.x, endNode.y, size);

        // Color based on region (Arm, Leg, Torso)
        paintLine.color = _getConnectionColor(idx0, idx1);
        canvas.drawLine(start, end, paintLine);
      }
    }

    // 2. Draw Landmarks (Joints)
    for (final landmark in pose!.landmarks) {
      if (landmark.visibility > 0.5) {
        final pos = _mapOffset(landmark.x, landmark.y, size);
        
        paintCircle.color = landmark.visibility > 0.8 
            ? AppColors.accent 
            : AppColors.accent.withOpacity(0.5);
            
        canvas.drawCircle(pos, 4.0, paintCircle);
      }
    }
  }

  Offset _mapOffset(double x, double y, Size size) {
    // Map normalized [0,1] to Canvas [width, height]
    // Note: On Android, the image might be rotated. 
    // This simple mapping assumes the preview matches the image aspect ratio.
    return Offset(x * size.width, y * size.height);
  }

  Color _getConnectionColor(int start, int end) {
    if ((start >= 11 && start <= 16) || (end >= 11 && end <= 16)) {
      return AppColors.armConnection;
    } else if ((start >= 23 && start <= 32) || (end >= 23 && end <= 32)) {
      return AppColors.legConnection;
    }
    return AppColors.torsoConnection;
  }

  @override
  bool shouldRepaint(SkeletonOverlay oldDelegate) {
    return oldDelegate.pose != pose;
  }
}
