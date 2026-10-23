import '../domain/models/reminder.dart';
import '../domain/models/repeat_type.dart';
import '../domain/services/ai_parser.dart';

/// Stage 01 fake parser: light Chinese heuristics + sensible defaults.
///
/// Does **not** call any AI API. Replace with HTTP + JSON schema in later stages.
class MockAiParser implements AiParser {
  MockAiParser({DateTime Function()? clock}) : _clock = clock ?? DateTime.now;

  final DateTime Function() _clock;

  @override
  Future<ParsedReminderDraft> parse(String text) async {
    // Simulate a short "thinking" delay for UX demo.
    await Future<void>.delayed(const Duration(milliseconds: 450));

    final trimmed = text.trim();
    final now = _clock();
    var dueAt = now.add(const Duration(hours: 1));
    var title = trimmed.isEmpty ? '新提醒' : trimmed;
    var repeatType = RepeatType.none;
    var repeatDays = <int>[];

    // 「10 分钟后」/ 「N分钟后」
    final minutesMatch =
        RegExp(r'(\d+)\s*分钟后').firstMatch(trimmed);
    if (minutesMatch != null) {
      final m = int.parse(minutesMatch.group(1)!);
      dueAt = now.add(Duration(minutes: m));
      title = _stripTimePhrases(trimmed);
    }

    // 「明天」→ full calendar date (not leave as relative)
    if (trimmed.contains('明天')) {
      final t = now.add(const Duration(days: 1));
      dueAt = DateTime(t.year, t.month, t.day, 9, 0);
      title = _stripTimePhrases(trimmed);
    }

    // 「后天」
    if (trimmed.contains('后天')) {
      final t = now.add(const Duration(days: 2));
      dueAt = DateTime(t.year, t.month, t.day, 9, 0);
      title = _stripTimePhrases(trimmed);
    }

    // 「今天下午四点半」/ 「三点」— Arabic or common Chinese numerals
    final hourMatch =
        RegExp(r'([零一二三四五六七八九十\d]{1,3})\s*点(半)?').firstMatch(trimmed);
    if (hourMatch != null) {
      var hour = _parseHourToken(hourMatch.group(1)!);
      final half = hourMatch.group(2) != null;
      if (trimmed.contains('下午') || trimmed.contains('晚上')) {
        if (hour > 0 && hour < 12) hour += 12;
      }
      if (hour >= 0 && hour <= 23) {
        dueAt = DateTime(dueAt.year, dueAt.month, dueAt.day, hour, half ? 30 : 0);
        title = _stripTimePhrases(trimmed);
      }
    }

    if (trimmed.contains('每天')) {
      repeatType = RepeatType.daily;
    } else if (trimmed.contains('每周')) {
      repeatType = RepeatType.weekly;
      repeatDays = [dueAt.weekday];
    }

    if (title.isEmpty || title == trimmed && trimmed.length > 40) {
      title = trimmed.length > 24 ? '${trimmed.substring(0, 24)}…' : trimmed;
    }
    if (title.isEmpty) title = '新提醒';

    return ParsedReminderDraft(
      title: title,
      dueAt: dueAt,
      rawText: trimmed,
      repeatType: repeatType,
      repeatDays: repeatDays,
    );
  }

  static String _stripTimePhrases(String text) {
    var t = text;
    t = t.replaceAll(RegExp(r'(\d+)\s*分钟后'), '');
    t = t.replaceAll(RegExp(r'明天|后天|今天'), '');
    t = t.replaceAll(
      RegExp(r'(上午|下午|晚上)?\s*[零一二三四五六七八九十\d]{1,3}\s*点(半)?'),
      '',
    );
    t = t.replaceAll(RegExp(r'提醒我|帮我|请'), '');
    t = t.replaceAll(RegExp(r'每天|每周'), '');
    t = t.trim();
    return t.isEmpty ? text.trim() : t;
  }

  static int _parseHourToken(String token) {
    final asInt = int.tryParse(token);
    if (asInt != null) return asInt;
    const map = {
      '零': 0,
      '一': 1,
      '二': 2,
      '两': 2,
      '三': 3,
      '四': 4,
      '五': 5,
      '六': 6,
      '七': 7,
      '八': 8,
      '九': 9,
      '十': 10,
    };
    if (token == '十') return 10;
    if (token.startsWith('十') && token.length == 2) {
      return 10 + (map[token[1]] ?? 0);
    }
    if (token.endsWith('十') && token.length == 2) {
      return (map[token[0]] ?? 0) * 10;
    }
    return map[token] ?? -1;
  }
}
