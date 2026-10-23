/** Reminder lifecycle status (PRD V1). */
export type ReminderStatus = 'pending' | 'completed' | 'cancelled'

/** How a reminder repeats. */
export type RepeatType = 'none' | 'daily' | 'weekly' | 'customWeekdays'

export const REPEAT_TYPE_LABELS: Record<RepeatType, string> = {
  none: '不重复',
  daily: '每天',
  weekly: '每周',
  customWeekdays: '自定义星期',
}

export const STATUS_LABELS: Record<ReminderStatus, string> = {
  pending: '待办',
  completed: '已完成',
  cancelled: '已取消',
}

/** Weekday short labels; index 0 unused — use 1=Mon … 7=Sun (JS Date.getDay remapped). */
export const WEEKDAY_SHORT = ['一', '二', '三', '四', '五', '六', '日'] as const

/** ISO-like weekday: 1=Mon … 7=Sun (matches Dart DateTime.weekday). */
export function toIsoWeekday(date: Date): number {
  const d = date.getDay() // 0=Sun … 6=Sat
  return d === 0 ? 7 : d
}

export function formatWeekdays(days: number[]): string {
  if (!days.length) return '未选择'
  return [...days]
    .sort((a, b) => a - b)
    .map((d) => `周${WEEKDAY_SHORT[d - 1]}`)
    .join('、')
}
