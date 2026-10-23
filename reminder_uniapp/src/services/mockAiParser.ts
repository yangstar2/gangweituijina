import type { ParsedReminderDraft } from '../domain/reminder'
import type { RepeatType } from '../domain/types'
import { toIsoWeekday } from '../domain/types'

/**
 * Stage 01 fake parser: light Chinese heuristics + sensible defaults.
 *
 * Does **not** call any AI API. Replace with HTTP + JSON schema in later stages.
 *
 * TODO(stage-03): real AI parser
 * - POST natural language to cloud/local model
 * - Validate response against Reminder JSON schema
 * - Never let AI call the notification scheduler directly
 */
export async function parseNaturalLanguage(
  text: string,
  clock: () => Date = () => new Date(),
): Promise<ParsedReminderDraft> {
  // Simulate a short "thinking" delay for UX demo.
  await delay(450)

  const trimmed = text.trim()
  const now = clock()
  let dueAt = new Date(now.getTime() + 60 * 60 * 1000)
  let title = trimmed || '新提醒'
  let repeatType: RepeatType = 'none'
  let repeatDays: number[] = []

  const minutesMatch = trimmed.match(/(\d+)\s*分钟后/)
  if (minutesMatch) {
    const m = Number(minutesMatch[1])
    dueAt = new Date(now.getTime() + m * 60 * 1000)
    title = stripTimePhrases(trimmed)
  }

  if (trimmed.includes('明天')) {
    const t = new Date(now)
    t.setDate(t.getDate() + 1)
    dueAt = new Date(t.getFullYear(), t.getMonth(), t.getDate(), 9, 0, 0, 0)
    title = stripTimePhrases(trimmed)
  }

  if (trimmed.includes('后天')) {
    const t = new Date(now)
    t.setDate(t.getDate() + 2)
    dueAt = new Date(t.getFullYear(), t.getMonth(), t.getDate(), 9, 0, 0, 0)
    title = stripTimePhrases(trimmed)
  }

  const hourMatch = trimmed.match(/([零一二三四五六七八九十两\d]{1,3})\s*点(半)?/)
  if (hourMatch) {
    let hour = parseHourToken(hourMatch[1])
    const half = Boolean(hourMatch[2])
    if (trimmed.includes('下午') || trimmed.includes('晚上')) {
      if (hour > 0 && hour < 12) hour += 12
    }
    if (hour >= 0 && hour <= 23) {
      dueAt = new Date(
        dueAt.getFullYear(),
        dueAt.getMonth(),
        dueAt.getDate(),
        hour,
        half ? 30 : 0,
        0,
        0,
      )
      title = stripTimePhrases(trimmed)
    }
  }

  if (trimmed.includes('每天')) {
    repeatType = 'daily'
  } else if (trimmed.includes('每周')) {
    repeatType = 'weekly'
    repeatDays = [toIsoWeekday(dueAt)]
  }

  if (!title || (title === trimmed && trimmed.length > 40)) {
    title = trimmed.length > 24 ? `${trimmed.slice(0, 24)}…` : trimmed
  }
  if (!title) title = '新提醒'

  return {
    title,
    dueAt: dueAt.toISOString(),
    rawText: trimmed,
    repeatType,
    repeatDays,
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function stripTimePhrases(text: string): string {
  let t = text
  t = t.replace(/(\d+)\s*分钟后/g, '')
  t = t.replace(/明天|后天|今天/g, '')
  t = t.replace(/(上午|下午|晚上)?\s*[零一二三四五六七八九十两\d]{1,3}\s*点(半)?/g, '')
  t = t.replace(/提醒我|帮我|请/g, '')
  t = t.replace(/每天|每周/g, '')
  t = t.trim()
  return t || text.trim()
}

function parseHourToken(token: string): number {
  const asInt = Number.parseInt(token, 10)
  if (!Number.isNaN(asInt)) return asInt
  const map: Record<string, number> = {
    零: 0,
    一: 1,
    二: 2,
    两: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9,
    十: 10,
  }
  if (token === '十') return 10
  if (token.startsWith('十') && token.length === 2) {
    return 10 + (map[token[1]] ?? 0)
  }
  if (token.endsWith('十') && token.length === 2) {
    return (map[token[0]] ?? 0) * 10
  }
  return map[token] ?? -1
}
