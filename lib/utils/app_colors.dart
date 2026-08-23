import 'package:flutter/material.dart';

class AppColors {
  // Primary Palette (Lush & Forest Greens)
  static const Color primary = Color(0xFF1B5E20); // Deep Forest Green
  static const Color primaryLight = Color(0xFF2E7D32); // Vibrant Farm Green
  static const Color primaryLighter = Color(0xFF4CAF50);
  static const Color primaryContainer = Color(0xFFE8F5E9);
  static const Color primaryDark = Color(0xFF0F3D12);

  // Secondary Palette (Harvest Amber & Gold)
  static const Color secondary = Color(0xFFF57F17); // Warm Harvest Gold
  static const Color secondaryLight = Color(0xFFFFB300);
  static const Color secondaryContainer = Color(0xFFFFF8E1);
  static const Color secondaryDark = Color(0xFFC66900);

  // Background & Surface
  static const Color background = Color(0xFFF6F8F5);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceVariant = Color(0xFFF1F5F0);
  static const Color cardBorder = Color(0xFFE2E8F0);

  // Text Colors
  static const Color textPrimary = Color(0xFF1E293B);
  static const Color textSecondary = Color(0xFF64748B);
  static const Color textMuted = Color(0xFF94A3B8);
  static const Color textOnPrimary = Color(0xFFFFFFFF);

  // Status & Feedback Colors
  static const Color success = Color(0xFF16A34A);
  static const Color successContainer = Color(0xFFDCFCE7);
  static const Color warning = Color(0xFFD97706);
  static const Color warningContainer = Color(0xFFFEF3C7);
  static const Color info = Color(0xFF0284C7);
  static const Color infoContainer = Color(0xFFE0F2FE);
  static const Color error = Color(0xFFDC2626);
  static const Color errorContainer = Color(0xFFFEE2E2);

  // Decorative Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFF1B5E20),
      Color(0xFF2E7D32),
    ],
  );

  static const LinearGradient harvestGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFFF57F17),
      Color(0xFFFFB300),
    ],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFFFFFFFF),
      Color(0xFFF8FAF7),
    ],
  );
}
