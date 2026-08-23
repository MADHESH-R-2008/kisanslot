import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:kisanslot/main.dart';
import 'package:kisanslot/models/booking.dart';
import 'package:kisanslot/services/mock_data_service.dart';

void main() {
  setUp(() {
    MockDataService().resetData();
    MockDataService().registerFarmer(
      name: 'Ravi Kumar',
      mobile: '9876543210',
      farmerId: 'FR10245',
      village: 'Example Village',
      district: 'Example District',
      state: 'Tamil Nadu',
      crop: 'Paddy',
      expectedQuantity: 850.0,
    );
  });

  testWidgets('End-to-end KisanSlot Phase 1 user journey test', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    // 1. Splash Screen
    await tester.pumpWidget(const KisanSlotApp());
    expect(find.text('KisanSlot'), findsOneWidget);
    expect(find.text('Book Smart. Wait Less.'), findsOneWidget);

    // Fast-forward splash animation & auto-navigation
    await tester.pump(const Duration(milliseconds: 2500));
    await tester.pumpAndSettle();

    // 2. Login Screen
    expect(find.text('Welcome Back 👋'), findsOneWidget);
    final loginBtn = find.text('LOGIN');
    expect(loginBtn, findsOneWidget);

    // Tap Login with default demo credentials
    await tester.tap(loginBtn);
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();

    // 3. Home Screen
    expect(find.text('Welcome to KisanSlot'), findsOneWidget);
    expect(find.text('Book Procurement Slot'), findsOneWidget);
    expect(find.text('Live Queue'), findsWidgets);
    expect(find.text('Procurement Status'), findsOneWidget);
    expect(find.text('Payment Status'), findsOneWidget);

    // 4. Navigate to Centre Selection
    final bookSlotCard = find.text('Book Procurement Slot');
    await tester.ensureVisible(bookSlotCard);
    await tester.tap(bookSlotCard);
    await tester.pumpAndSettle();

    expect(find.text('Select Procurement Centre'), findsOneWidget);
    expect(find.text('Centre B'), findsWidgets);

    // 5. Select Centre B & View Slots
    final viewSlotsButtons = find.text('View Slots');
    expect(viewSlotsButtons, findsWidgets);
    await tester.ensureVisible(viewSlotsButtons.at(1));
    await tester.tap(viewSlotsButtons.at(1)); // Tap Centre B
    await tester.pumpAndSettle();

    // 6. Slot Booking Screen
    expect(find.text('Book Procurement Slot'), findsOneWidget);
    expect(find.text('Selected Centre'), findsOneWidget);
    final confirmBtn = find.text('CONFIRM BOOKING');
    await tester.ensureVisible(confirmBtn);
    expect(confirmBtn, findsOneWidget);

    // Tap confirm booking
    await tester.tap(confirmBtn);
    await tester.pump(const Duration(milliseconds: 800));
    await tester.pumpAndSettle();

    // 7. Booking Confirmation Screen
    expect(find.text('Booking Confirmed!'), findsOneWidget);
    expect(find.text('#17'), findsOneWidget);
    final viewQueueBtn = find.text('VIEW LIVE QUEUE');
    await tester.ensureVisible(viewQueueBtn);
    expect(viewQueueBtn, findsOneWidget);

    // 8. Navigate to Live Queue Screen
    await tester.tap(viewQueueBtn);
    await tester.pumpAndSettle();

    expect(find.text('Live Queue'), findsOneWidget);
    expect(find.text('YOUR QUEUE POSITION'), findsOneWidget);
    expect(find.text('#17'), findsOneWidget);
    final refreshBtn = find.text('REFRESH QUEUE');
    await tester.ensureVisible(refreshBtn);
    expect(refreshBtn, findsOneWidget);

    // Test Refresh Queue Action
    await tester.tap(refreshBtn);
    await tester.pump(const Duration(milliseconds: 600));
    await tester.pumpAndSettle();

    // Queue advances to #12
    expect(find.text('#12'), findsOneWidget);
  });

  testWidgets('MockDataService state and queue progression test', (WidgetTester tester) async {
    final service = MockDataService();
    final initialBooking = service.activeBooking;
    expect(initialBooking, isNotNull);
    expect(initialBooking!.queuePosition, 17);

    // Refresh queue step 1
    service.refreshQueue();
    expect(service.activeBooking!.queuePosition, 12);
    expect(service.activeBooking!.farmersAhead, 11);

    // Refresh queue step 2
    service.refreshQueue();
    expect(service.activeBooking!.queuePosition, 8);

    // Refresh queue step 3
    service.refreshQueue();
    expect(service.activeBooking!.queuePosition, 5);

    // Refresh queue step 4
    service.refreshQueue();
    expect(service.activeBooking!.queuePosition, 2);

    // Refresh queue step 5 (Your turn)
    service.refreshQueue();
    expect(service.activeBooking!.queuePosition, 1);
    expect(service.activeBooking!.status, BookingStatus.atCounter);
  });
}
