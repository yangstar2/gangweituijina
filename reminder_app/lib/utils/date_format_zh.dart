import 'package:intl/intl.dart';

import '../domain/models/repeat_type.dart';

/// Chinese-friendly absolute date/time (never leave bare「明天」in confirm UI).
abstract final class DateFormatZh {
  static final DateFormat _full =
      DateFormat('yyyy年M月d日 EEEE HH:mm', 'zh_CN');
  static final DateFormat _date = DateFormat('yyyy年M月d日 EEEE', 'zh_CN');
  static final DateFormat _time = DateFormat('HH:mm', 'zh_CN');
  static final DateFormat _short = DateFormat('M月d日 HH:mm', 'zh_CN');

  static String fullDateTime(DateTime dt) => _full.format(dt);

  static String fullDate(DateTime dt) => _date.format(dt);

  static String timeOnly(DateTime dt) => _time.format(dt);

  static String shortDateTime(DateTime dt) => _short.format(dt);

  static String repeatSummary(RepeatType type, List<int> days) {
    switch (type) {
      case RepeatType.none:
        return '不重复';
      case RepeatType.daily:
        return '每天';
      case RepeatType.weekly:
        if (days.isEmpty) return '每周';
        return '每周 · ${WeekdayLabels.formatDays(days)}';
      case RepeatType.customWeekdays:
        return WeekdayLabels.formatDays(days);
    }
  }

  static String greeting(DateTime now) {
    final h = now.hour;
    if (h < 6) return '夜深了';
    if (h < 12) return '早上好';
    if (h < 14) return '中午好';
    if (h < 18) return '下午好';
    return '晚上好';
  }
}
