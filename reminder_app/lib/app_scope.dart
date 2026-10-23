import 'package:flutter/material.dart';

import 'data/in_memory_reminder_repository.dart';
import 'data/mock_ai_parser.dart';
import 'data/noop_notification_scheduler.dart';
import 'domain/services/ai_parser.dart';
import 'domain/services/notification_scheduler.dart';

/// Dependency container for Stage 01 (simple InheritedWidget, no DI framework).
class AppScope extends InheritedWidget {
  const AppScope({
    super.key,
    required this.repository,
    required this.aiParser,
    required this.notificationScheduler,
    required super.child,
  });

  final InMemoryReminderRepository repository;
  final AiParser aiParser;
  final NotificationScheduler notificationScheduler;

  static AppScope of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<AppScope>();
    assert(scope != null, 'AppScope not found');
    return scope!;
  }

  static AppScope read(BuildContext context) {
    final scope = context.getInheritedWidgetOfExactType<AppScope>();
    assert(scope != null, 'AppScope not found');
    return scope!;
  }

  @override
  bool updateShouldNotify(AppScope oldWidget) {
    return repository != oldWidget.repository ||
        aiParser != oldWidget.aiParser ||
        notificationScheduler != oldWidget.notificationScheduler;
  }
}

AppScope buildDefaultScope({required Widget child}) {
  return AppScope(
    repository: InMemoryReminderRepository(),
    aiParser: MockAiParser(),
    notificationScheduler: NoOpNotificationScheduler(),
    child: child,
  );
}
