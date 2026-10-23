import '../models/reminder.dart';

/// Port: schedule / cancel / reschedule local system notifications.
///
/// Stage 01: [NoOpNotificationScheduler] (no real alarms).
/// Stage 02: flutter_local_notifications + exact alarm / boot receiver.
///
/// Invariant (later stages): persist to SQLite **before** schedule;
/// on delete/edit, update DB then cancel/reschedule.
///
/// TODO(stage-02): request POST_NOTIFICATIONS + SCHEDULE_EXACT_ALARM;
/// TODO(stage-02): re-hydrate pending reminders after device reboot.
abstract class NotificationScheduler {
  Future<void> schedule(Reminder reminder);

  Future<void> cancel(String reminderId);

  Future<void> reschedule(Reminder reminder);

  Future<void> cancelAll();
}
