import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:talent_lens_ai/main.dart';

void main() {
  testWidgets('App launches and shows splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: TalentLensApp()),
    );
    // The splash screen should display the initialize button
    expect(find.text('INITIALIZE SYSTEM'), findsOneWidget);
  });
}
