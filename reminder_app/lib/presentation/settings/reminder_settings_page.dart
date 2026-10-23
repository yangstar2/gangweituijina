import 'package:flutter/material.dart';

import '../../domain/models/reminder.dart';
import '../../domain/models/repeat_type.dart';
import '../../theme/app_theme.dart';
import '../../utils/date_format_zh.dart';

/// Edit date / time / repeat (none · daily · weekly · custom weekdays).
class ReminderSettingsPage extends StatefulWidget {
  const ReminderSettingsPage({
    super.key,
    required this.initial,
    this.title = '提醒设置',
  });

  final ParsedReminderDraft initial;
  final String title;

  @override
  State<ReminderSettingsPage> createState() => _ReminderSettingsPageState();
}

class _ReminderSettingsPageState extends State<ReminderSettingsPage> {
  late TextEditingController _titleController;
  late DateTime _dueAt;
  late RepeatType _repeatType;
  late Set<int> _repeatDays;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.initial.title);
    _dueAt = widget.initial.dueAt;
    _repeatType = widget.initial.repeatType;
    _repeatDays = {...widget.initial.repeatDays};
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueAt,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365 * 3)),
      locale: const Locale('zh', 'CN'),
      helpText: '选择日期',
      cancelText: '取消',
      confirmText: '确定',
    );
    if (picked == null) return;
    setState(() {
      _dueAt = DateTime(
        picked.year,
        picked.month,
        picked.day,
        _dueAt.hour,
        _dueAt.minute,
      );
    });
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_dueAt),
      helpText: '选择时间',
      cancelText: '取消',
      confirmText: '确定',
      builder: (context, child) {
        return Localizations.override(
          context: context,
          locale: const Locale('zh', 'CN'),
          child: child,
        );
      },
    );
    if (picked == null) return;
    setState(() {
      _dueAt = DateTime(
        _dueAt.year,
        _dueAt.month,
        _dueAt.day,
        picked.hour,
        picked.minute,
      );
    });
  }

  void _save() {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请填写提醒标题')),
      );
      return;
    }
    if (_repeatType == RepeatType.customWeekdays && _repeatDays.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请至少选择一个星期')),
      );
      return;
    }
    final days = switch (_repeatType) {
      RepeatType.none || RepeatType.daily => <int>[],
      RepeatType.weekly =>
        _repeatDays.isEmpty ? <int>[_dueAt.weekday] : _repeatDays.toList()
          ..sort(),
      RepeatType.customWeekdays => (_repeatDays.toList()..sort()),
    };
    Navigator.of(context).pop(
      ParsedReminderDraft(
        title: title,
        dueAt: _dueAt,
        rawText: widget.initial.rawText,
        repeatType: _repeatType,
        repeatDays: days,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          Text(
            '标题',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkMuted,
                ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(hintText: '提醒内容'),
          ),
          const SizedBox(height: 22),
          Text(
            '日期',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkMuted,
                ),
          ),
          const SizedBox(height: 8),
          _PickerTile(
            icon: Icons.calendar_today_outlined,
            label: DateFormatZh.fullDate(_dueAt),
            onTap: _pickDate,
          ),
          const SizedBox(height: 16),
          Text(
            '时间',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkMuted,
                ),
          ),
          const SizedBox(height: 8),
          _PickerTile(
            icon: Icons.access_time,
            label: DateFormatZh.timeOnly(_dueAt),
            onTap: _pickTime,
          ),
          const SizedBox(height: 22),
          Text(
            '重复',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkMuted,
                ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: RepeatType.values.map((t) {
              final selected = _repeatType == t;
              return ChoiceChip(
                label: Text(t.labelZh),
                selected: selected,
                onSelected: (_) {
                  setState(() {
                    _repeatType = t;
                    if (t == RepeatType.weekly && _repeatDays.isEmpty) {
                      _repeatDays = {_dueAt.weekday};
                    }
                  });
                },
                selectedColor: AppColors.teal,
                labelStyle: TextStyle(
                  color: selected ? Colors.white : AppColors.ink,
                  fontWeight: FontWeight.w600,
                ),
              );
            }).toList(),
          ),
          if (_repeatType == RepeatType.customWeekdays ||
              _repeatType == RepeatType.weekly) ...[
            const SizedBox(height: 16),
            Text(
              '选择星期',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppColors.inkMuted,
                  ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List.generate(7, (i) {
                final day = i + 1;
                final selected = _repeatDays.contains(day);
                return FilterChip(
                  label: Text('周${WeekdayLabels.short[i]}'),
                  selected: selected,
                  onSelected: (v) {
                    setState(() {
                      if (v) {
                        _repeatDays.add(day);
                      } else {
                        _repeatDays.remove(day);
                      }
                    });
                  },
                  selectedColor: AppColors.tealSoft,
                  checkmarkColor: AppColors.tealDeep,
                );
              }),
            ),
          ],
          const SizedBox(height: 28),
          FilledButton(
            onPressed: _save,
            child: const Text('完成'),
          ),
        ],
      ),
    );
  }
}

class _PickerTile extends StatelessWidget {
  const _PickerTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surfaceElevated,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFD0E0DE)),
          ),
          child: Row(
            children: [
              Icon(icon, color: AppColors.teal),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.inkMuted),
            ],
          ),
        ),
      ),
    );
  }
}
