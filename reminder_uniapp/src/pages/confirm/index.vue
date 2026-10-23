<template>
  <view v-if="draft" class="page">
    <text class="lead">请核对解析结果</text>
    <text class="hint">日期会显示完整年月日，方便确认。</text>

    <view class="card">
      <view class="row">
        <text class="label">标题</text>
        <text class="value">{{ draft.title || '新提醒' }}</text>
      </view>
      <view class="row">
        <text class="label">日期</text>
        <text class="value">{{ fullDate(draft.dueAt) }}</text>
      </view>
      <view class="row">
        <text class="label">时间</text>
        <text class="value">{{ timeOnly(draft.dueAt) }}</text>
      </view>
      <view class="row">
        <text class="label">重复</text>
        <text class="value">{{ repeatSummary(draft.repeatType, draft.repeatDays) }}</text>
      </view>
      <view v-if="draft.rawText" class="row">
        <text class="label">原文</text>
        <text class="value muted">{{ draft.rawText }}</text>
      </view>
    </view>

    <view class="actions">
      <button class="btn outline" :disabled="saving" @click="onEdit">修改</button>
      <button class="btn primary" :loading="saving" :disabled="saving" @click="onSave">
        确认保存
      </button>
    </view>
  </view>
  <view v-else class="page empty-wrap">
    <text class="empty">没有待确认的草稿，请返回首页重新创建。</text>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { createReminder, type ParsedReminderDraft } from '../../domain/reminder'
import { reminderStore } from '../../store/reminders'
import { fullDate, repeatSummary, timeOnly } from '../../utils/dateFormatZh'

const draft = ref<ParsedReminderDraft | null>(null)
const saving = ref(false)

onShow(() => {
  draft.value = reminderStore.draft ? { ...reminderStore.draft } : null
})

function onEdit() {
  if (!draft.value) return
  reminderStore.setDraft(draft.value, '修改提醒')
  uni.navigateTo({ url: '/pages/settings/index?mode=edit-draft' })
}

async function onSave() {
  if (!draft.value) return
  saving.value = true
  try {
    const d = draft.value
    if (d.editId) {
      const existing = reminderStore.getById(d.editId)
      if (existing) {
        await reminderStore.update({
          ...existing,
          title: d.title || '新提醒',
          dueAt: d.dueAt,
          rawText: d.rawText,
          repeatType: d.repeatType,
          repeatDays: d.repeatDays,
        })
      }
    } else {
      await reminderStore.add(
        createReminder({
          title: d.title || '新提醒',
          dueAt: d.dueAt,
          rawText: d.rawText,
          repeatType: d.repeatType,
          repeatDays: d.repeatDays,
        }),
      )
    }
    reminderStore.setDraft(null)
    uni.showToast({ title: '已保存到待办（内存，重启后丢失）', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack({ delta: 1 })
    }, 400)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx 40rpx 48rpx;
  background: #f3f8f7;
}

.lead {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: #1a3a38;
}

.hint {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #6b8582;
}

.card {
  margin-top: 32rpx;
  padding: 8rpx 28rpx;
  background: #fff;
  border-radius: 20rpx;
  border: 1rpx solid rgba(26, 95, 90, 0.08);
}

.row {
  display: flex;
  flex-direction: row;
  gap: 24rpx;
  padding: 28rpx 0;
  border-bottom: 1rpx solid rgba(26, 95, 90, 0.06);
}

.row:last-child {
  border-bottom: none;
}

.label {
  width: 100rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  color: #6b8582;
  font-weight: 600;
}

.value {
  flex: 1;
  font-size: 28rpx;
  color: #1a3a38;
  font-weight: 600;
  line-height: 1.4;
}

.value.muted {
  font-weight: 400;
  color: #4a6b67;
}

.actions {
  display: flex;
  flex-direction: row;
  gap: 20rpx;
  margin-top: 48rpx;
}

.btn {
  flex: 1;
  border-radius: 16rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.btn.outline {
  background: #fff;
  color: #1a7a72;
  border: 2rpx solid #1a7a72;
}

.btn.primary {
  background: #1a7a72;
  color: #fff;
  border: none;
}

.empty-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty {
  color: #8aa3a0;
  font-size: 28rpx;
}
</style>
