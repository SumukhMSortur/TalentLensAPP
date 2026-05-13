import 'package:flutter/material.dart';
import '../../ui/theme/app_colors.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('SETTINGS')),
      body: const Center(
        child: Text('System settings coming soon...'),
      ),
    );
  }
}
