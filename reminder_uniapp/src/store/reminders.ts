import { computed, reactive } from 'vue'
import {
  createReminder,
  type ParsedReminderDraft,
  type Reminder,
} from '../domain/reminder'
import type { ReminderStatus } from '../domain/types'
import { noopNotificationScheduler } from '../services/notificationScheduler'
import { isSameLocalDay } from '../utils/dateFormatZh'

function seedReminders(now = new Date()): Reminder[] {
  const y = now.getFullYear()
  const m = now.getMonth()
  const d = now.getDate()

  const plusDays = (days: number, hour: number, minute: number) => {
    const t = new Date(y, m, d + days, hour, minute, 0, 0)
    return t.toISOString()
  }

  return [
    createReminder({
      id: 'seed-1',
      title: '交数学作业',
      dueAt: new Date(y, m, d, 16, 30, 0, 0).toISOString(),
      rawText: '今天下午四点半提醒我交数学作业',
      status: 'pending',
      createdAt: new Date(now.getTime() - 2 * 3600_000).toISOString(),
    }),
    createReminder({
      id: 'seed-2',
      title: '英语口语练习',
      dueAt: new Date(y, m, d, 19, 0, 0, 0).toISOString(),
      rawText: '晚上七点练英语口语',
      repeatType: 'daily',
      status: 'pending',
      createdAt: new Date(now.getTime() - 86400_000).toISOString(),
    }),
    createReminder({
      id: 'seed-3',
      title: '家长会',
      dueAt: plusDays(2, 18, 30),
      rawText: '后天晚上六点半家长会',
      status: 'pending',
      createdAt: new Date(now.getTime() - 5 * 3600_000).toISOString(),
    }),
    createReminder({
      id: 'seed-4',
      title: '整理书包',
      dueAt: new Date(y, m, d - 1, 7, 30, 0, 0).toISOString(),
      status: 'completed',
      createdAt: new Date(now.getTime() - 2 * 86400_000).toISOString(),
      updatedAt: new Date(now.getTime() - 12 * 3600_000).toISOString(),
    }),
    createReminder({
      id: 'seed-5',
      title: '跑步 20 分钟',
      dueAt: plusDays(1, 6, 30),
      repeatType: 'customWeekdays',
      repeatDays: [1, 3, 5],
      status: 'pending',
      createdAt: new Date(now.getTime() - 3 * 86400_000).toISOString(),
    }),
  ]
}

const state = reactive({
  items: seedReminders() as Reminder[],
  seq: 100,
  /** Draft passed between home → confirm → settings. */
  draft: null as ParsedReminderDraft | null,
  settingsTitle: '提醒设置',
})

export const reminderStore = {
  get items(): Reminder[] {
    return state.items
  },

  get draft(): ParsedReminderDraft | null {
    return state.draft
  },

  get settingsTitle(): string {
    return state.settingsTitle
  },

  setDraft(draft: ParsedReminderDraft | null, settingsTitle = '提醒设置') {
    state.draft = draft
    state.settingsTitle = settingsTitle
  },

  getById(id: string): Reminder | undefined {
    return state.items.find((r) => r.id === id)
  },

  getByStatus(status: ReminderStatus): Reminder[] {
    return state.items.filter((r) => r.status === status)
  },

  todayPending(now = new Date()): Reminder[] {
    return state.items
      .filter((r) => r.status === 'pending' && isSameLocalDay(new Date(r.dueAt), now))
      .sort((a, b) => +new Date(a.dueAt) - +new Date(b.dueAt))
  },

  upcomingPending(now = new Date()): Reminder[] {
    const endToday = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      23,
      59,
      59,
      999,
    )
    return state.items
      .filter((r) => r.status === 'pending' && new Date(r.dueAt) > endToday)
      .sort((a, b) => +new Date(a.dueAt) - +new Date(b.dueAt))
  },

  completed(): Reminder[] {
    return state.items
      .filter((r) => r.status === 'completed')
      .sort((a, b) => +new Date(b.dueAt) - +new Date(a.dueAt))
  },

  async add(reminder: Reminder): Promise<Reminder> {
    const withId =
      reminder.id && reminder.id.length > 0
        ? reminder
        : {
            ...reminder,
            id: `local-${state.seq++}`,
            createdAt: reminder.createdAt ?? new Date().toISOString(),
          }
    state.items = [...state.items, withId]
    await noopNotificationScheduler.schedule(withId)
    return withId
  },

  async update(reminder: Reminder): Promise<Reminder> {
    const i = state.items.findIndex((r) => r.id === reminder.id)
    if (i < 0) throw new Error(`Reminder not found: ${reminder.id}`)
    const updated = { ...reminder, updatedAt: new Date().toISOString() }
    const next = [...state.items]
    next[i] = updated
    state.items = next
    await noopNotificationScheduler.reschedule(updated)
    return updated
  },

  async remove(id: string): Promise<void> {
    await noopNotificationScheduler.cancel(id)
    state.items = state.items.filter((r) => r.id !== id)
  },

  async complete(id: string): Promise<Reminder> {
    const existing = this.getById(id)
    if (!existing) throw new Error(`Reminder not found: ${id}`)
    await noopNotificationScheduler.cancel(id)
    return this.update({ ...existing, status: 'completed' })
  },
}

/** Reactive helpers for Vue components (auto-track state.items). */
export function useReminderLists() {
  const today = computed(() => reminderStore.todayPending())
  const upcoming = computed(() => reminderStore.upcomingPending())
  const done = computed(() => reminderStore.completed())
  const pending = computed(() =>
    [...reminderStore.getByStatus('pending')].sort(
      (a, b) => +new Date(a.dueAt) - +new Date(b.dueAt),
    ),
  )
  const completedList = computed(() => reminderStore.completed())
  return { today, upcoming, done, pending, completedList }
}
