import 'package:flutter_test/flutter_test.dart';
import 'package:kisanslot/main.dart';

void main() {
  testWidgets('KisanSlot app renders splash screen smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const KisanSlotApp());

    // Verify initial splash screen text
    expect(find.text('KisanSlot'), findsOneWidget);
    expect(find.text('Book Smart. Wait Less.'), findsOneWidget);

    // Fast-forward time past splash timer (2.2s)
    await tester.pump(const Duration(milliseconds: 2500));
    await tester.pumpAndSettle();

    // Verify navigation to Login screen
    expect(find.text('Welcome Back 👋'), findsOneWidget);
    expect(find.text('LOGIN'), findsOneWidget);
  });
}
