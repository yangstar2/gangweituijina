<template>
  <view class="page">
    <text class="field-label">标题</text>
    <input
      v-model="title"
      class="field-input"
      maxlength="80"
      placeholder="提醒内容"
      placeholder-class="ph"
    />

    <text class="field-label">日期</text>
    <picker mode="date" :value="dateStr" @change="onDateChange">
      <view class="picker-tile">
        <text>{{ fullDate(previewIso) }}</text>
        <text class="chev">›</text>
      </view>
    </picker>

    <text class="field-label">时间</text>
    <picker mode="time" :value="timeStr" @change="onTimeChange">
      <view class="picker-tile">
        <text>{{ timeStr }}</text>
        <text class="chev">›</text>
      </view>
    </picker>

    <text class="field-label">重复</text>
    <view class="repeat-wrap">
      <view
        v-for="opt in repeatOptions"
        :key="opt.value"
        class="repeat-chip"
        :class="{ active: repeatType === opt.value }"
        @click="onRepeat(opt.value)"
      >
        {{ opt.label }}
      </view>
    </view>

    <view v-if="repeatType === 'weekly' || repeatType === 'customWeekdays'" class="weekdays">
      <text class="field-label">选择星期</text>
      <view class="weekday-row">
        <view
          v-for="d in 7"
          :key="d"
          class="day"
          :class="{ active: repeatDays.includes(d) }"
          @click="toggleDay(d)"
        >
          {{ WEEKDAY_SHORT[d - 1] }}
        </view>
      </view>
    </view>

    <button class="save-btn" @click="onSave">保存</button>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import type { RepeatType } from '../../domain/types'
import { REPEAT_TYPE_LABELS, WEEKDAY_SHORT, toIsoWeekday } from '../../domain/types'
import { reminderStore } from '../../store/reminders'
import {
  combineDateAndTime,
  fullDate,
  toDateInputValue,
  toTimeInputValue,
} from '../../utils/dateFormatZh'

const title = ref('')
const dateStr = ref('')
const timeStr = ref('')
const repeatType = ref<RepeatType>('none')
const repeatDays = ref<number[]>([])
const rawText = ref<string | undefined>()
const editId = ref<string | undefined>()
const mode = ref('edit-draft')

const repeatOptions = (Object.keys(REPEAT_TYPE_LABELS) as RepeatType[]).map((value) => ({
  value,
  label: REPEAT_TYPE_LABELS[value],
}))

const previewIso = computed(() => combineDateAndTime(dateStr.value, timeStr.value))

onLoad((query) => {
  mode.value = (query?.mode as string) || 'edit-draft'
  const draft = reminderStore.draft
  const due = draft?.dueAt ? new Date(draft.dueAt) : new Date(Date.now() + 3600_000)
  title.value = draft?.title ?? ''
  dateStr.value = toDateInputValue(due)
  timeStr.value = toTimeInputValue(due)
  repeatType.value = draft?.repeatType ?? 'none'
  repeatDays.value = [...(draft?.repeatDays ?? [])]
  rawText.value = draft?.rawText
  editId.value = draft?.editId

  const navTitle = reminderStore.settingsTitle || '提醒设置'
  uni.setNavigationBarTitle({ title: navTitle })
})

function onDateChange(e: { detail: { value: string } }) {
  dateStr.value = e.detail.value
}

function onTimeChange(e: { detail: { value: string } }) {
  timeStr.value = e.detail.value
}

function onRepeat(t: RepeatType) {
  repeatType.value = t
  if (t === 'weekly' && !repeatDays.value.length) {
    repeatDays.value = [toIsoWeekday(new Date(previewIso.value))]
  }
}

function toggleDay(d: number) {
  if (repeatDays.value.includes(d)) {
    repeatDays.value = repeatDays.value.filter((x) => x !== d)
  } else {
    repeatDays.value = [...repeatDays.value, d].sort((a, b) => a - b)
  }
}

async function onSave() {
  const t = title.value.trim()
  if (!t) {
    uni.showToast({ title: '请填写提醒标题', icon: 'none' })
    return
  }
  if (repeatType.value === 'customWeekdays' && !repeatDays.value.length) {
    uni.showToast({ title: '请至少选择一个星期', icon: 'none' })
    return
  }

  let days: number[] = []
  if (repeatType.value === 'weekly') {
    days = repeatDays.value.length
      ? [...repeatDays.value].sort((a, b) => a - b)
      : [toIsoWeekday(new Date(previewIso.value))]
  } else if (repeatType.value === 'customWeekdays') {
    days = [...repeatDays.value].sort((a, b) => a - b)
  }

  const nextDraft = {
    title: t,
    dueAt: previewIso.value,
    rawText: rawText.value,
    repeatType: repeatType.value,
    repeatDays: days,
    editId: editId.value,
  }

  if (mode.value === 'edit-item' && editId.value) {
    const existing = reminderStore.getById(editId.value)
    if (existing) {
      await reminderStore.update({
        ...existing,
        title: nextDraft.title,
        dueAt: nextDraft.dueAt,
        rawText: nextDraft.rawText,
        repeatType: nextDraft.repeatType,
        repeatDays: nextDraft.repeatDays,
      })
      reminderStore.setDraft(null)
      uni.showToast({ title: '已更新', icon: 'none' })
      setTimeout(() => uni.navigateBack({ delta: 1 }), 300)
      return
    }
  }

  // create / edit-draft → back to confirm
  reminderStore.setDraft(nextDraft)
  if (mode.value === 'create') {
    uni.redirectTo({ url: '/pages/confirm/index' })
  } else {
    uni.navigateBack({ delta: 1 })
  }
}
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 28rpx 40rpx 64rpx;
  background: #f3f8f7;
}

.field-label {
  display: block;
  margin: 28rpx 0 12rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: #6b8582;
}

.field-input {
  padding: 22rpx 24rpx;
  background: #fff;
  border-radius: 16rpx;
  font-size: 30rpx;
  color: #1a3a38;
  border: 1rpx solid rgba(26, 95, 90, 0.1);
}

.ph {
  color: #9bb0ad;
}

.picker-tile {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 26rpx 24rpx;
  background: #fff;
  border-radius: 16rpx;
  font-size: 30rpx;
  color: #1a3a38;
  border: 1rpx solid rgba(26, 95, 90, 0.1);
}

.chev {
  color: #9bb0ad;
  font-size: 36rpx;
}

.repeat-wrap {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 14rpx;
}

.repeat-chip {
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  background: #fff;
  color: #1a3a38;
  font-size: 26rpx;
  border: 1rpx solid rgba(26, 95, 90, 0.12);
}

.repeat-chip.active {
  background: #1a7a72;
  color: #fff;
  border-color: #1a7a72;
}

.weekday-row {
  display: flex;
  flex-direction: row;
  gap: 12rpx;
  flex-wrap: wrap;
}

.day {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #1a3a38;
  font-size: 26rpx;
  font-weight: 600;
  border: 1rpx solid rgba(26, 95, 90, 0.12);
}

.day.active {
  background: #1a7a72;
  color: #fff;
  border-color: #1a7a72;
}

.save-btn {
  margin-top: 56rpx;
  background: #1a7a72;
  color: #fff;
  border-radius: 16rpx;
  font-size: 30rpx;
  font-weight: 700;
  border: none;
}
</style>
