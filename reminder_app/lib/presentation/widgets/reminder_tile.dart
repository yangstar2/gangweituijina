import 'package:flutter/material.dart';

import '../../domain/models/reminder.dart';
import '../../domain/models/repeat_type.dart';
import '../../theme/app_theme.dart';
import '../../utils/date_format_zh.dart';

class ReminderTile extends StatelessWidget {
  const ReminderTile({
    super.key,
    required this.reminder,
    this.onTap,
    this.onComplete,
    this.onEdit,
    this.onDelete,
    this.showActions = false,
  });

  final Reminder reminder;
  final VoidCallback? onTap;
  final VoidCallback? onComplete;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final bool showActions;

  @override
  Widget build(BuildContext context) {
    final muted = reminder.isCompleted;
    return Material(
      color: AppColors.surfaceElevated,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 10, 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 4,
                height: 48,
                margin: const EdgeInsets.only(right: 12, top: 2),
                decoration: BoxDecoration(
                  color: muted ? AppColors.inkMuted.withValues(alpha: 0.35) : AppColors.teal,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      reminder.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            decoration:
                                muted ? TextDecoration.lineThrough : null,
                            color: muted ? AppColors.inkMuted : AppColors.ink,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      DateFormatZh.shortDateTime(reminder.dueAt),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.inkMuted,
                          ),
                    ),
                    if (reminder.repeatType != RepeatType.none) ...[
                      const SizedBox(height: 4),
                      Text(
                        DateFormatZh.repeatSummary(
                          reminder.repeatType,
                          reminder.repeatDays,
                        ),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.tealDeep,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
              if (showActions)
                PopupMenuButton<String>(
                  onSelected: (v) {
                    switch (v) {
                      case 'edit':
                        onEdit?.call();
                      case 'complete':
                        onComplete?.call();
                      case 'delete':
                        onDelete?.call();
                    }
                  },
                  itemBuilder: (context) => [
                    if (reminder.isPending)
                      const PopupMenuItem(value: 'complete', child: Text('完成')),
                    const PopupMenuItem(value: 'edit', child: Text('编辑')),
                    const PopupMenuItem(value: 'delete', child: Text('删除')),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }
}
