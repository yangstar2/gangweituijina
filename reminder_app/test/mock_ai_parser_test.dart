import 'package:flutter_test/flutter_test.dart';
import 'package:reminder_app/data/mock_ai_parser.dart';
import 'package:reminder_app/domain/models/repeat_type.dart';

void main() {
  test('parses 10 minutes later into absolute dueAt', () async {
    final now = DateTime(2026, 10, 23, 10, 0);
    final parser = MockAiParser(clock: () => now);
    final draft = await parser.parse('10 分钟后提醒我休息一下');
    expect(draft.dueAt, DateTime(2026, 10, 23, 10, 10));
    expect(draft.title, isNot(contains('分钟后')));
  });

  test('明天 becomes full calendar date', () async {
    final now = DateTime(2026, 10, 23, 10, 0);
    final parser = MockAiParser(clock: () => now);
    final draft = await parser.parse('明天下午三点交作业');
    expect(draft.dueAt.year, 2026);
    expect(draft.dueAt.month, 10);
    expect(draft.dueAt.day, 24);
    expect(draft.dueAt.hour, 15);
  });

  test('每天 sets daily repeat', () async {
    final parser = MockAiParser(clock: () => DateTime(2026, 10, 23));
    final draft = await parser.parse('每天早上跑步');
    expect(draft.repeatType, RepeatType.daily);
  });
}
