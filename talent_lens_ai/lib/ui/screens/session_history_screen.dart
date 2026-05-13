import 'package:flutter/material.dart';
import '../../ui/theme/app_colors.dart';

class SessionHistoryScreen extends StatelessWidget {
  const SessionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('HISTORY')),
      body: const Center(
        child: Text('Session history coming soon...'),
      ),
    );
  }
}
