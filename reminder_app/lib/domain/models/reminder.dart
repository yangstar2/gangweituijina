import 'repeat_type.dart';
import 'reminder_status.dart';

/// Domain entity for a personal reminder (PRD fields for V1).
///
/// Stage 01: in-memory only. Stage 02+ will persist via SQLite.
class Reminder {
  const Reminder({
    required this.id,
    required this.title,
    required this.dueAt,
    this.rawText,
    this.repeatType = RepeatType.none,
    this.repeatDays = const [],
    this.status = ReminderStatus.pending,
    this.createdAt,
    this.updatedAt,
  });

  final String id;

  /// Display title (from AI parse or manual edit).
  final String title;

  /// Absolute date-time when the reminder should fire.
  final DateTime dueAt;

  /// Original natural-language input, if any.
  final String? rawText;

  final RepeatType repeatType;

  /// For [RepeatType.customWeekdays] / weekly: Dart weekdays 1–7.
  final List<int> repeatDays;

  final ReminderStatus status;

  final DateTime? createdAt;
  final DateTime? updatedAt;

  bool get isPending => status == ReminderStatus.pending;
  bool get isCompleted => status == ReminderStatus.completed;

  Reminder copyWith({
    String? id,
    String? title,
    DateTime? dueAt,
    String? rawText,
    RepeatType? repeatType,
    List<int>? repeatDays,
    ReminderStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Reminder(
      id: id ?? this.id,
      title: title ?? this.title,
      dueAt: dueAt ?? this.dueAt,
      rawText: rawText ?? this.rawText,
      repeatType: repeatType ?? this.repeatType,
      repeatDays: repeatDays ?? this.repeatDays,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

/// Draft produced by AI parse (or mock) before the user confirms save.
class ParsedReminderDraft {
  const ParsedReminderDraft({
    required this.title,
    required this.dueAt,
    this.rawText,
    this.repeatType = RepeatType.none,
    this.repeatDays = const [],
  });

  final String title;
  final DateTime dueAt;
  final String? rawText;
  final RepeatType repeatType;
  final List<int> repeatDays;

  ParsedReminderDraft copyWith({
    String? title,
    DateTime? dueAt,
    String? rawText,
    RepeatType? repeatType,
    List<int>? repeatDays,
  }) {
    return ParsedReminderDraft(
      title: title ?? this.title,
      dueAt: dueAt ?? this.dueAt,
      rawText: rawText ?? this.rawText,
      repeatType: repeatType ?? this.repeatType,
      repeatDays: repeatDays ?? this.repeatDays,
    );
  }
}
