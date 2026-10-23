import type { Reminder } from '../domain/reminder'

/**
 * Local notification scheduler port.
 *
 * Stage 01: no-op stub — logs only. Do NOT schedule real system notifications yet.
 *
 * TODO(stage-02): App-Plus / Android exact alarm + local notification
 * - Request POST_NOTIFICATIONS (Android 13+)
 * - Request SCHEDULE_EXACT_ALARM / 闹钟与提醒授权 when needed
 * - On boot: rehydrate pending reminders from SQLite and reschedule
 * - schedule / cancel / reschedule must stay in App layer (never AI)
 */
export interface NotificationScheduler {
  schedule(reminder: Reminder): Promise<void>
  cancel(reminderId: string): Promise<void>
  reschedule(reminder: Reminder): Promise<void>
}

export const noopNotificationScheduler: NotificationScheduler = {
  async schedule(reminder) {
    console.info('[notificationScheduler:stub] schedule', reminder.id, reminder.dueAt)
  },
  async cancel(reminderId) {
    console.info('[notificationScheduler:stub] cancel', reminderId)
  },
  async reschedule(reminder) {
    console.info('[notificationScheduler:stub] reschedule', reminder.id, reminder.dueAt)
  },
}
