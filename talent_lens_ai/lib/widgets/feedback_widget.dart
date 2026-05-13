import 'package:flutter/material.dart';
import '../models/feedback_model.dart';
import '../ui/theme/app_colors.dart';

class FeedbackWidget extends StatelessWidget {
  final List<FeedbackItem> feedbackItems;

  const FeedbackWidget({super.key, required this.feedbackItems});

  @override
  Widget build(BuildContext context) {
    if (feedbackItems.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: feedbackItems.map((item) => _buildFeedbackCard(context, item)).toList(),
      ),
    );
  }

  Widget _buildFeedbackCard(BuildContext context, FeedbackItem item) {
    final color = _getSeverityColor(item.severity);
    final icon = _getSeverityIcon(item.severity);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (item.affectedJoint != null)
                  Text(
                    item.affectedJoint!.toUpperCase(),
                    style: TextStyle(
                      fontFamily: 'Rajdhani',
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: color,
                      letterSpacing: 1.0,
                    ),
                  ),
                Text(
                  item.message,
                  style: const TextStyle(
                    fontFamily: 'DM Sans',
                    fontSize: 14,
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getSeverityColor(FeedbackSeverity severity) {
    switch (severity) {
      case FeedbackSeverity.good:
        return AppColors.success;
      case FeedbackSeverity.warning:
        return AppColors.warning;
      case FeedbackSeverity.critical:
        return AppColors.error;
    }
  }

  IconData _getSeverityIcon(FeedbackSeverity severity) {
    switch (severity) {
      case FeedbackSeverity.good:
        return Icons.check_circle_outline;
      case FeedbackSeverity.warning:
        return Icons.warning_amber_rounded;
      case FeedbackSeverity.critical:
        return Icons.error_outline_rounded;
    }
  }
}
