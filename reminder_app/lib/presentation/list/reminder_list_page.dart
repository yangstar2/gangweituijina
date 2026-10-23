import 'package:flutter/material.dart';

import '../../app_scope.dart';
import '../../domain/models/reminder.dart';
import '../../domain/models/reminder_status.dart';
import '../../theme/app_theme.dart';
import '../confirm/parse_confirm_page.dart';
import '../settings/reminder_settings_page.dart';
import '../widgets/reminder_tile.dart';

enum _ListFilter { pending, completed }

class ReminderListPage extends StatefulWidget {
  const ReminderListPage({super.key});

  @override
  State<ReminderListPage> createState() => _ReminderListPageState();
}

class _ReminderListPageState extends State<ReminderListPage> {
  _ListFilter _filter = _ListFilter.pending;

  Future<void> _edit(Reminder reminder) async {
    final draft = ParsedReminderDraft(
      title: reminder.title,
      dueAt: reminder.dueAt,
      rawText: reminder.rawText,
      repeatType: reminder.repeatType,
      repeatDays: reminder.repeatDays,
    );
    final edited = await Navigator.of(context).push<ParsedReminderDraft>(
      MaterialPageRoute(
        builder: (_) => ReminderSettingsPage(
          initial: draft,
          title: '编辑提醒',
        ),
      ),
    );
    if (edited == null || !mounted) return;
    final scope = AppScope.read(context);
    final updated = reminder.copyWith(
      title: edited.title,
      dueAt: edited.dueAt,
      repeatType: edited.repeatType,
      repeatDays: edited.repeatDays,
      rawText: edited.rawText,
    );
    await scope.repository.update(updated);
    await scope.notificationScheduler.reschedule(updated);
  }

  Future<void> _delete(Reminder reminder) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除提醒？'),
        content: Text('确定删除「${reminder.title}」吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    final scope = AppScope.read(context);
    await scope.notificationScheduler.cancel(reminder.id);
    await scope.repository.delete(reminder.id);
  }

  Future<void> _complete(Reminder reminder) async {
    final scope = AppScope.read(context);
    await scope.repository.complete(reminder.id);
    await scope.notificationScheduler.cancel(reminder.id);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已完成：${reminder.title}')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final repo = AppScope.of(context).repository;
    return ListenableBuilder(
      listenable: repo,
      builder: (context, _) {
        final items = _filter == _ListFilter.pending
            ? repo.getByStatus(ReminderStatus.pending)
            : repo.getByStatus(ReminderStatus.completed);
        final sorted = [...items]
          ..sort((a, b) => a.dueAt.compareTo(b.dueAt));

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '全部提醒',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                          color: AppColors.tealDeep,
                        ),
                  ),
                  const SizedBox(height: 12),
                  SegmentedButton<_ListFilter>(
                    segments: const [
                      ButtonSegment(
                        value: _ListFilter.pending,
                        label: Text('待办'),
                        icon: Icon(Icons.checklist_rtl, size: 18),
                      ),
                      ButtonSegment(
                        value: _ListFilter.completed,
                        label: Text('已完成'),
                        icon: Icon(Icons.done_all, size: 18),
                      ),
                    ],
                    selected: {_filter},
                    onSelectionChanged: (s) {
                      setState(() => _filter = s.first);
                    },
                  ),
                ],
              ),
            ),
            Expanded(
              child: sorted.isEmpty
                  ? Center(
                      child: Text(
                        _filter == _ListFilter.pending
                            ? '暂无待办'
                            : '还没有已完成的提醒',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              color: AppColors.inkMuted,
                            ),
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                      itemCount: sorted.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 10),
                      itemBuilder: (context, i) {
                        final r = sorted[i];
                        return ReminderTile(
                          reminder: r,
                          showActions: true,
                          onEdit: () => _edit(r),
                          onDelete: () => _delete(r),
                          onComplete:
                              r.isPending ? () => _complete(r) : null,
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => ParseConfirmPage(
                                  draft: ParsedReminderDraft(
                                    title: r.title,
                                    dueAt: r.dueAt,
                                    rawText: r.rawText,
                                    repeatType: r.repeatType,
                                    repeatDays: r.repeatDays,
                                  ),
                                ),
                              ),
                            );
                          },
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }
}
