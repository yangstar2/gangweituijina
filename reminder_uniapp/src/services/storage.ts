import type { Reminder } from '../domain/reminder'

/**
 * Persistence port (SQLite / uni.storage).
 *
 * Stage 01: unused — data lives in the in-memory store only.
 *
 * TODO(stage-02): SQLite (or uni-app plus SQLite / sqlite plugin)
 * - Schema: reminders(id, title, due_at, raw_text, repeat_type, repeat_days, status, …)
 * - Load all on launch; write-through on CRUD
 * - After persist success → notificationScheduler.schedule
 * - On delete/complete → cancel notification then delete/update row
 */
export interface ReminderStorage {
  loadAll(): Promise<Reminder[]>
  upsert(reminder: Reminder): Promise<void>
  remove(id: string): Promise<void>
}

/** Placeholder so imports resolve; Stage 01 must not call this for real I/O. */
export const stubReminderStorage: ReminderStorage = {
  async loadAll() {
    console.info('[storage:stub] loadAll — Stage 01 uses in-memory store only')
    return []
  },
  async upsert(reminder) {
    console.info('[storage:stub] upsert', reminder.id)
  },
  async remove(id) {
    console.info('[storage:stub] remove', id)
  },
}
