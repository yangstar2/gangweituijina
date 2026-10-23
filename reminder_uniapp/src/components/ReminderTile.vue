<template>
  <view class="tile" @click="$emit('tap', reminder)">
    <view class="tile-main">
      <text class="tile-title" :class="{ done: reminder.status === 'completed' }">
        {{ reminder.title }}
      </text>
      <text class="tile-meta">{{ shortDateTime(reminder.dueAt) }} · {{ repeatLabel }}</text>
    </view>
    <view v-if="showActions" class="tile-actions">
      <text v-if="reminder.status === 'pending'" class="action" @click.stop="$emit('complete', reminder)">完成</text>
      <text class="action" @click.stop="$emit('edit', reminder)">编辑</text>
      <text class="action danger" @click.stop="$emit('delete', reminder)">删除</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Reminder } from '../domain/reminder'
import { repeatSummary, shortDateTime } from '../utils/dateFormatZh'

const props = withDefaults(
  defineProps<{
    reminder: Reminder
    showActions?: boolean
  }>(),
  { showActions: false },
)

defineEmits<{
  tap: [reminder: Reminder]
  edit: [reminder: Reminder]
  delete: [reminder: Reminder]
  complete: [reminder: Reminder]
}>()

const repeatLabel = computed(() =>
  repeatSummary(props.reminder.repeatType, props.reminder.repeatDays),
)
</script>

<style scoped lang="scss">
.tile {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 24rpx 28rpx;
  background: #ffffff;
  border-radius: 20rpx;
  border: 1rpx solid rgba(26, 95, 90, 0.08);
  box-shadow: 0 6rpx 20rpx rgba(26, 95, 90, 0.05);
}

.tile-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tile-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1a3a38;
  line-height: 1.35;
}

.tile-title.done {
  color: #8aa3a0;
  text-decoration: line-through;
}

.tile-meta {
  font-size: 24rpx;
  color: #6b8582;
}

.tile-actions {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 12rpx;
  justify-content: flex-end;
  max-width: 280rpx;
}

.action {
  font-size: 24rpx;
  color: #1a7a72;
  padding: 8rpx 12rpx;
}

.action.danger {
  color: #c45c4a;
}
</style>
