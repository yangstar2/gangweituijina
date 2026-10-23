import '../domain/models/reminder.dart';
import '../domain/services/notification_scheduler.dart';

/// Stage 01: no-op scheduler. Logs intent only — no system alarms.
class NoOpNotificationScheduler implements NotificationScheduler {
  @override
  Future<void> schedule(Reminder reminder) async {
    // ignore: avoid_print
    print(
      '[NotificationScheduler stub] schedule id=${reminder.id} '
      'at=${reminder.dueAt.toIso8601String()} title=${reminder.title}',
    );
  }

  @override
  Future<void> cancel(String reminderId) async {
    // ignore: avoid_print
    print('[NotificationScheduler stub] cancel id=$reminderId');
  }

  @override
  Future<void> reschedule(Reminder reminder) async {
    await cancel(reminder.id);
    await schedule(reminder);
  }

  @override
  Future<void> cancelAll() async {
    // ignore: avoid_print
    print('[NotificationScheduler stub] cancelAll');
  }
}
