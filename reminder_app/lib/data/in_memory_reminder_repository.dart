import 'package:flutter/foundation.dart';

import '../domain/models/reminder.dart';
import '../domain/models/reminder_status.dart';
import '../domain/models/repeat_type.dart';
import '../domain/repositories/reminder_repository.dart';

/// Stage 01 in-memory store with seed mock data.
class InMemoryReminderRepository extends ChangeNotifier
    implements ReminderRepository {
  InMemoryReminderRepository({DateTime? now}) {
    final n = now ?? DateTime.now();
    _items = [
      Reminder(
        id: 'seed-1',
        title: '交数学作业',
        dueAt: DateTime(n.year, n.month, n.day, 16, 30),
        rawText: '今天下午四点半提醒我交数学作业',
        status: ReminderStatus.pending,
        createdAt: n.subtract(const Duration(hours: 2)),
      ),
      Reminder(
        id: 'seed-2',
        title: '英语口语练习',
        dueAt: DateTime(n.year, n.month, n.day, 19, 0),
        rawText: '晚上七点练英语口语',
        repeatType: RepeatType.daily,
        status: ReminderStatus.pending,
        createdAt: n.subtract(const Duration(days: 1)),
      ),
      Reminder(
        id: 'seed-3',
        title: '家长会',
        dueAt: n.add(const Duration(days: 2)).copyWith(
              hour: 18,
              minute: 30,
              second: 0,
              millisecond: 0,
              microsecond: 0,
            ),
        rawText: '后天晚上六点半家长会',
        status: ReminderStatus.pending,
        createdAt: n.subtract(const Duration(hours: 5)),
      ),
      Reminder(
        id: 'seed-4',
        title: '整理书包',
        dueAt: DateTime(n.year, n.month, n.day, 7, 30)
            .subtract(const Duration(days: 1)),
        status: ReminderStatus.completed,
        createdAt: n.subtract(const Duration(days: 2)),
        updatedAt: n.subtract(const Duration(hours: 12)),
      ),
      Reminder(
        id: 'seed-5',
        title: '跑步 20 分钟',
        dueAt: n.add(const Duration(days: 1)).copyWith(
              hour: 6,
              minute: 30,
              second: 0,
              millisecond: 0,
              microsecond: 0,
            ),
        repeatType: RepeatType.customWeekdays,
        repeatDays: const [1, 3, 5],
        status: ReminderStatus.pending,
        createdAt: n.subtract(const Duration(days: 3)),
      ),
    ];
  }

  late List<Reminder> _items;
  int _seq = 100;

  @override
  List<Reminder> getAll() => List.unmodifiable(_items);

  @override
  List<Reminder> getByStatus(ReminderStatus status) =>
      _items.where((r) => r.status == status).toList(growable: false);

  @override
  Reminder? getById(String id) {
    for (final r in _items) {
      if (r.id == id) return r;
    }
    return null;
  }

  @override
  Future<Reminder> add(Reminder reminder) async {
    final withId = reminder.id.isEmpty
        ? reminder.copyWith(
            id: 'local-${_seq++}',
            createdAt: reminder.createdAt ?? DateTime.now(),
          )
        : reminder;
    _items = [..._items, withId];
    notifyListeners();
    return withId;
  }

  @override
  Future<Reminder> update(Reminder reminder) async {
    final i = _items.indexWhere((r) => r.id == reminder.id);
    if (i < 0) {
      throw StateError('Reminder not found: ${reminder.id}');
    }
    final updated = reminder.copyWith(updatedAt: DateTime.now());
    _items = [..._items]..[i] = updated;
    notifyListeners();
    return updated;
  }

  @override
  Future<void> delete(String id) async {
    _items = _items.where((r) => r.id != id).toList();
    notifyListeners();
  }

  @override
  Future<Reminder> complete(String id) async {
    final existing = getById(id);
    if (existing == null) {
      throw StateError('Reminder not found: $id');
    }
    return update(existing.copyWith(status: ReminderStatus.completed));
  }

  /// Today's pending items (calendar day local).
  List<Reminder> todayPending({DateTime? now}) {
    final n = now ?? DateTime.now();
    return _items
        .where(
          (r) =>
              r.isPending &&
              r.dueAt.year == n.year &&
              r.dueAt.month == n.month &&
              r.dueAt.day == n.day,
        )
        .toList()
      ..sort((a, b) => a.dueAt.compareTo(b.dueAt));
  }

  /// Upcoming pending beyond today.
  List<Reminder> upcomingPending({DateTime? now}) {
    final n = now ?? DateTime.now();
    final endToday = DateTime(n.year, n.month, n.day, 23, 59, 59);
    return _items
        .where((r) => r.isPending && r.dueAt.isAfter(endToday))
        .toList()
      ..sort((a, b) => a.dueAt.compareTo(b.dueAt));
  }

  List<Reminder> completed({DateTime? now}) {
    return _items.where((r) => r.isCompleted).toList()
      ..sort((a, b) => b.dueAt.compareTo(a.dueAt));
  }
}
