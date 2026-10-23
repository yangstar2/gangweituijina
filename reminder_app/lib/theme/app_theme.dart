import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Student-friendly teal + amber palette (avoid purple-AI cliché).
abstract final class AppColors {
  static const Color tealDeep = Color(0xFF0B6E6E);
  static const Color teal = Color(0xFF148C8C);
  static const Color tealSoft = Color(0xFFD6EEEE);
  static const Color amber = Color(0xFFE09A2B);
  static const Color amberSoft = Color(0xFFFFF1D6);
  static const Color ink = Color(0xFF1C2B2B);
  static const Color inkMuted = Color(0xFF5A6B6B);
  static const Color surface = Color(0xFFF3F8F7);
  static const Color surfaceElevated = Color(0xFFFFFFFF);
  static const Color danger = Color(0xFFC44536);
  static const Color success = Color(0xFF2F8F5B);
}

ThemeData buildAppTheme() {
  final baseText = GoogleFonts.notoSansScTextTheme();
  final colorScheme = ColorScheme.light(
    primary: AppColors.teal,
    onPrimary: Colors.white,
    secondary: AppColors.amber,
    onSecondary: AppColors.ink,
    surface: AppColors.surfaceElevated,
    onSurface: AppColors.ink,
    error: AppColors.danger,
    onError: Colors.white,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    scaffoldBackgroundColor: AppColors.surface,
    textTheme: baseText.apply(
      bodyColor: AppColors.ink,
      displayColor: AppColors.ink,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: GoogleFonts.notoSansSc(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      ),
      iconTheme: const IconThemeData(color: AppColors.ink),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.teal,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: GoogleFonts.notoSansSc(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.tealDeep,
        side: const BorderSide(color: AppColors.teal, width: 1.4),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: GoogleFonts.notoSansSc(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceElevated,
      hintStyle: GoogleFonts.notoSansSc(color: AppColors.inkMuted),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFD0E0DE)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: AppColors.teal, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.tealSoft,
      selectedColor: AppColors.teal,
      labelStyle: GoogleFonts.notoSansSc(fontSize: 13, color: AppColors.ink),
      secondaryLabelStyle:
          GoogleFonts.notoSansSc(fontSize: 13, color: Colors.white),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      side: BorderSide.none,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppColors.surfaceElevated,
      indicatorColor: AppColors.tealSoft,
      labelTextStyle: WidgetStatePropertyAll(
        GoogleFonts.notoSansSc(fontSize: 12, fontWeight: FontWeight.w600),
      ),
    ),
  );
}
