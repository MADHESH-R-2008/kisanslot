import 'package:flutter/material.dart';
import '../models/centre.dart';
import '../models/booking.dart';
import '../screens/splash_screen.dart';
import '../screens/login_screen.dart';
import '../screens/register_screen.dart';
import '../screens/home_screen.dart';
import '../screens/centre_screen.dart';
import '../screens/slot_booking_screen.dart';
import '../screens/booking_confirmation_screen.dart';
import '../screens/queue_screen.dart';
import '../screens/procurement_screen.dart';
import '../screens/payment_screen.dart';
import '../screens/profile_screen.dart';
import '../screens/notification_screen.dart';
import '../screens/admin_home_screen.dart';
import '../screens/admin_procurement_screen.dart';

class AppRoutes {
  static const String splash = '/';
  static const String login = '/login';
  static const String register = '/register';
  static const String home = '/home';
  static const String centre = '/centre';
  static const String slotBooking = '/slot_booking';
  static const String confirmation = '/confirmation';
  static const String queue = '/queue';
  static const String procurement = '/procurement';
  static const String payment = '/payment';
  static const String profile = '/profile';
  static const String notification = '/notifications';
  static const String adminHome = '/admin/home';
  static const String adminProcurement = '/admin/procurement';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      case login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case register:
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      case home:
        return MaterialPageRoute(builder: (_) => const HomeScreen());
      case centre:
        return PageRouteBuilder(
          pageBuilder: (_, _, _) => const CentreScreen(),
          transitionDuration: Duration.zero,
          reverseTransitionDuration: Duration.zero,
        );
      case slotBooking:
        final centre = settings.arguments as ProcurementCentre?;
        if (centre == null) {
          return MaterialPageRoute(builder: (_) => const Scaffold(body: Center(child: Text('Select a procurement centre first.'))));
        }
        return MaterialPageRoute(
          builder: (_) => SlotBookingScreen(selectedCentre: centre),
        );
      case confirmation:
        final booking = settings.arguments as BookingModel?;
        if (booking == null) {
          return MaterialPageRoute(builder: (_) => const Scaffold(body: Center(child: Text('Booking details are unavailable.'))));
        }
        return MaterialPageRoute(
          builder: (_) => BookingConfirmationScreen(booking: booking),
        );
      case queue:
        return MaterialPageRoute(builder: (_) => const QueueScreen());
      case procurement:
        final bookingId = settings.arguments as String?;
        return MaterialPageRoute(builder: (_) => ProcurementScreen(bookingId: bookingId));
      case payment:
        final bookingId = settings.arguments as String?;
        return MaterialPageRoute(builder: (_) => PaymentScreen(bookingId: bookingId));
      case profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());
      case notification:
        return MaterialPageRoute(builder: (_) => const NotificationScreen());
      case adminHome:
        return MaterialPageRoute(builder: (_) => const AdminHomeScreen());
      case adminProcurement:
        final bookingId = settings.arguments as String?;
        return MaterialPageRoute(builder: (_) => AdminProcurementScreen(bookingId: bookingId ?? ''));
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(
              child: Text('No route defined for ${settings.name}'),
            ),
          ),
        );
    }
  }
}
