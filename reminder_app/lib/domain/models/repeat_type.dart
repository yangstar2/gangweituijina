/// How a reminder repeats.
enum RepeatType {
  none,
  daily,
  weekly,
  customWeekdays,
}

extension RepeatTypeLabel on RepeatType {
  String get labelZh {
    switch (this) {
      case RepeatType.none:
        return '不重复';
      case RepeatType.daily:
        return '每天';
      case RepeatType.weekly:
        return '每周';
      case RepeatType.customWeekdays:
        return '自定义星期';
    }
  }
}

/// Weekday helpers: Dart [DateTime.weekday] is 1=Mon … 7=Sun.
abstract final class WeekdayLabels {
  static const List<String> short = [
    '一',
    '二',
    '三',
    '四',
    '五',
    '六',
    '日',
  ];

  static String formatDays(List<int> days) {
    if (days.isEmpty) return '未选择';
    final sorted = [...days]..sort();
    return sorted.map((d) => '周${short[d - 1]}').join('、');
  }
}
