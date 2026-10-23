import 'package:flutter/material.dart';

import '../../app_scope.dart';
import '../../domain/models/reminder.dart';
import '../../theme/app_theme.dart';
import '../../utils/date_format_zh.dart';
import '../settings/reminder_settings_page.dart';

/// AI parse confirm: show full date (not relative「明天」), time, repeat.
class ParseConfirmPage extends StatefulWidget {
  const ParseConfirmPage({super.key, required this.draft});

  final ParsedReminderDraft draft;

  @override
  State<ParseConfirmPage> createState() => _ParseConfirmPageState();
}

class _ParseConfirmPageState extends State<ParseConfirmPage> {
  late ParsedReminderDraft _draft;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _draft = widget.draft;
  }

  Future<void> _edit() async {
    final edited = await Navigator.of(context).push<ParsedReminderDraft>(
      MaterialPageRoute(
        builder: (_) => ReminderSettingsPage(
          initial: _draft,
          title: '修改提醒',
        ),
      ),
    );
    if (edited != null && mounted) {
      setState(() => _draft = edited);
    }
  }

  Future<void> _confirmSave() async {
    setState(() => _saving = true);
    try {
      final scope = AppScope.read(context);
      final reminder = Reminder(
        id: '',
        title: _draft.title.isEmpty ? '新提醒' : _draft.title,
        dueAt: _draft.dueAt,
        rawText: _draft.rawText,
        repeatType: _draft.repeatType,
        repeatDays: _draft.repeatDays,
      );
      final saved = await scope.repository.add(reminder);
      // Stage 01: stub only — no real system notification.
      await scope.notificationScheduler.schedule(saved);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已保存到待办（内存，重启后丢失）')),
      );
      Navigator.of(context).pop(true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('确认提醒'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          Text(
            '请核对解析结果',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: 6),
          Text(
            '日期会显示完整年月日，方便确认。',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.inkMuted,
                ),
          ),
          const SizedBox(height: 20),
          _InfoCard(
            children: [
              _InfoRow(label: '标题', value: _draft.title),
              _InfoRow(
                label: '日期',
                value: DateFormatZh.fullDate(_draft.dueAt),
              ),
              _InfoRow(
                label: '时间',
                value: DateFormatZh.timeOnly(_draft.dueAt),
              ),
              _InfoRow(
                label: '重复',
                value: DateFormatZh.repeatSummary(
                  _draft.repeatType,
                  _draft.repeatDays,
                ),
              ),
              if (_draft.rawText != null && _draft.rawText!.isNotEmpty)
                _InfoRow(label: '原文', value: _draft.rawText!),
            ],
          ),
          const SizedBox(height: 28),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _saving ? null : _edit,
                  child: const Text('修改'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: _saving ? null : _confirmSave,
                  child: _saving
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.4,
                            color: Colors.white,
                          ),
                        )
                      : const Text('确认保存'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD0E0DE)),
      ),
      child: Column(children: children),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 56,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.inkMuted,
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
