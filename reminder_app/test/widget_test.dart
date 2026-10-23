import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:reminder_app/app_scope.dart';
import 'package:reminder_app/data/in_memory_reminder_repository.dart';
import 'package:reminder_app/data/mock_ai_parser.dart';
import 'package:reminder_app/data/noop_notification_scheduler.dart';
import 'package:reminder_app/main.dart';
import 'package:reminder_app/presentation/shell/main_shell.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('zh_CN');
  });

  testWidgets('Home shows brand and NL input', (tester) async {
    await tester.pumpWidget(
      AppScope(
        repository: InMemoryReminderRepository(
          now: DateTime(2026, 10, 23, 10, 0),
        ),
        aiParser: MockAiParser(clock: () => DateTime(2026, 10, 23, 10, 0)),
        notificationScheduler: NoOpNotificationScheduler(),
        child: const ReminderApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('AI 个人提醒助手'), findsOneWidget);
    expect(find.textContaining('想提醒什么'), findsOneWidget);
    expect(find.text('10 分钟后'), findsOneWidget);
    expect(find.text('指定时间'), findsOneWidget);
    expect(find.text('今日待办'), findsOneWidget);
  });

  testWidgets('Bottom nav switches to list', (tester) async {
    await tester.pumpWidget(
      AppScope(
        repository: InMemoryReminderRepository(
          now: DateTime(2026, 10, 23, 10, 0),
        ),
        aiParser: MockAiParser(),
        notificationScheduler: NoOpNotificationScheduler(),
        child: const MaterialApp(home: MainShell()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('提醒'));
    await tester.pumpAndSettle();
    expect(find.text('全部提醒'), findsOneWidget);
    expect(find.text('待办'), findsWidgets);
  });
}
