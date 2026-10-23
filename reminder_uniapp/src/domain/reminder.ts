import type { ReminderStatus, RepeatType } from './types'

/**
 * Domain entity for a personal reminder (PRD fields for V1).
 * Stage 01: in-memory only. Stage 02+ will persist via SQLite.
 */
export interface Reminder {
  id: string
  /** Display title (from AI parse or manual edit). */
  title: string
  /** Absolute date-time when the reminder should fire (ISO string). */
  dueAt: string
  /** Original natural-language input, if any. */
  rawText?: string
  repeatType: RepeatType
  /** For weekly / customWeekdays: 1=Mon … 7=Sun. */
  repeatDays: number[]
  status: ReminderStatus
  createdAt?: string
  updatedAt?: string
}

/** Draft produced by AI parse (or mock) before the user confirms save. */
export interface ParsedReminderDraft {
  title: string
  dueAt: string
  rawText?: string
  repeatType: RepeatType
  repeatDays: number[]
  /** When editing an existing reminder, keep its id. */
  editId?: string
}

export function createReminder(partial: {
  id?: string
  title: string
  dueAt: string
  rawText?: string
  repeatType?: RepeatType
  repeatDays?: number[]
  status?: ReminderStatus
  createdAt?: string
  updatedAt?: string
}): Reminder {
  return {
    id: partial.id ?? '',
    title: partial.title,
    dueAt: partial.dueAt,
    rawText: partial.rawText,
    repeatType: partial.repeatType ?? 'none',
    repeatDays: partial.repeatDays ?? [],
    status: partial.status ?? 'pending',
    createdAt: partial.createdAt,
    updatedAt: partial.updatedAt,
  }
}

export function isPending(r: Reminder): boolean {
  return r.status === 'pending'
}

export function isCompleted(r: Reminder): boolean {
  return r.status === 'completed'
}
