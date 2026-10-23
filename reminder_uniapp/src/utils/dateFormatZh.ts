import type { RepeatType } from '../domain/types'
import { formatWeekdays } from '../domain/types'

const WEEKDAY_FULL = [
  '星期日',
  '星期一',
  '星期二',
  '星期三',
  '星期四',
  '星期五',
  '星期六',
]

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n)
}

export function fullDate(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${WEEKDAY_FULL[d.getDay()]}`
}

export function timeOnly(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
}

export function shortDateTime(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${d.getMonth() + 1}月${d.getDate()}日 ${timeOnly(d)}`
}

export function fullDateTime(iso: string | Date): string {
  return `${fullDate(iso)} ${timeOnly(iso)}`
}

export function repeatSummary(type: RepeatType, days: number[]): string {
  switch (type) {
    case 'none':
      return '不重复'
    case 'daily':
      return '每天'
    case 'weekly':
      return days.length ? `每周 · ${formatWeekdays(days)}` : '每周'
    case 'customWeekdays':
      return formatWeekdays(days)
  }
}

export function greeting(now = new Date()): string {
  const h = now.getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
}

export function toDateInputValue(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

export function toTimeInputValue(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
}

export function combineDateAndTime(dateStr: string, timeStr: string): string {
  const [y, m, day] = dateStr.split('-').map(Number)
  const [hh, mm] = timeStr.split(':').map(Number)
  return new Date(y, m - 1, day, hh, mm, 0, 0).toISOString()
}

export function isSameLocalDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}
