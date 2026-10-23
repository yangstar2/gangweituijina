import '../models/reminder.dart';
import '../models/reminder_status.dart';

/// Persistence port for reminders.
///
/// Stage 01: [InMemoryReminderRepository].
/// Stage 02+: SQLite implementation — keep this interface stable.
abstract class ReminderRepository {
  List<Reminder> getAll();

  List<Reminder> getByStatus(ReminderStatus status);

  Reminder? getById(String id);

  Future<Reminder> add(Reminder reminder);

  Future<Reminder> update(Reminder reminder);

  Future<void> delete(String id);

  Future<Reminder> complete(String id);

  /// Subscribe to list changes (UI rebuild).
  void addListener(void Function() listener);

  void removeListener(void Function() listener);
}
