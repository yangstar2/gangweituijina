/// Lifecycle status of a reminder item.
enum ReminderStatus {
  pending,
  completed,
  cancelled,
}

extension ReminderStatusLabel on ReminderStatus {
  String get labelZh {
    switch (this) {
      case ReminderStatus.pending:
        return '待办';
      case ReminderStatus.completed:
        return '已完成';
      case ReminderStatus.cancelled:
        return '已取消';
    }
  }
}
