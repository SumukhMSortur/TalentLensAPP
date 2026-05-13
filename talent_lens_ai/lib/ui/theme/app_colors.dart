import 'package:flutter/material.dart';

class AppColors {
  // Brand Colors
  static const Color background = Color(0xFF0A0E1A); // Deep navy
  static const Color surface = Color(0xFF151B2D);    // Lighter navy
  static const Color accent = Color(0xFF00E5FF);     // Neon Cyan
  static const Color secondary = Color(0xFF7C4DFF);  // Deep Purple
  static const Color highlight = Color(0xFFFF6B35);  // Energy Orange

  // Functional Colors
  static const Color success = Color(0xFF00E676);    // Green
  static const Color warning = Color(0xFFFFD600);    // Amber
  static const Color error = Color(0xFFFF5252);      // Red
  static const Color info = Color(0xFF2979FF);       // Blue

  // Skeleton / Region Colors
  static const Color armConnection = accent;
  static const Color legConnection = success;
  static const Color torsoConnection = Colors.white;

  // Text Colors
  static const Color textPrimary = Colors.white;
  static const Color textSecondary = Color(0xFFB0B0B0);
  static const Color textMuted = Color(0xFF606060);

  // Gradients
  static const Gradient primaryGradient = LinearGradient(
    colors: [accent, secondary],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const Gradient scoreGradient = SweepGradient(
    colors: [error, warning, success],
    stops: [0.0, 0.5, 1.0],
  );
}
