import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'utils/app_theme.dart';
import 'utils/routes.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // CRITICAL FIX: Disable runtime font fetching to prevent mid-frame async
  // HTTP loads from triggering layout rebuilds during semantics computation,
  // which causes the !semantics.parentDataDirty assertion crash.
  GoogleFonts.config.allowRuntimeFetching = false;

  // Set system UI overlay style for seamless top bar
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(const KisanSlotApp());
}

class KisanSlotApp extends StatelessWidget {
  const KisanSlotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KisanSlot',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      initialRoute: AppRoutes.splash,
      onGenerateRoute: AppRoutes.onGenerateRoute,
    );
  }
}
