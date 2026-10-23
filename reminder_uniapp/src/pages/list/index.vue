<template>
  <view class="page">
    <text class="heading">全部提醒</text>

    <view class="filters">
      <view
        class="filter"
        :class="{ active: filter === 'pending' }"
        @click="filter = 'pending'"
      >
        待办
      </view>
      <view
        class="filter"
        :class="{ active: filter === 'completed' }"
        @click="filter = 'completed'"
      >
        已完成
      </view>
    </view>

    <view v-if="!items.length" class="empty">
      {{ filter === 'pending' ? '暂无待办' : '还没有已完成的提醒' }}
    </view>

    <ReminderTile
      v-for="r in items"
      :key="r.id"
      class="tile-gap"
      :reminder="r"
      show-actions
      @edit="onEdit"
      @delete="onDelete"
      @complete="onComplete"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ReminderTile from '../../components/ReminderTile.vue'
import type { Reminder } from '../../domain/reminder'
import { reminderStore, useReminderLists } from '../../store/reminders'

const filter = ref<'pending' | 'completed'>('pending')
const { pending, completedList } = useReminderLists()

const items = computed(() =>
  filter.value === 'pending' ? pending.value : completedList.value,
)

function onEdit(reminder: Reminder) {
  reminderStore.setDraft(
    {
      title: reminder.title,
      dueAt: reminder.dueAt,
      rawText: reminder.rawText,
      repeatType: reminder.repeatType,
      repeatDays: [...reminder.repeatDays],
      editId: reminder.id,
    },
    '编辑提醒',
  )
  uni.navigateTo({ url: '/pages/settings/index?mode=edit-item' })
}

function onDelete(reminder: Reminder) {
  uni.showModal({
    title: '删除提醒？',
    content: `确定删除「${reminder.title}」吗？`,
    confirmText: '删除',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      await reminderStore.remove(reminder.id)
      uni.showToast({ title: '已删除', icon: 'none' })
    },
  })
}

async function onComplete(reminder: Reminder) {
  await reminderStore.complete(reminder.id)
  uni.showToast({ title: `已完成：${reminder.title}`, icon: 'none' })
}
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx 40rpx 48rpx;
  background: #f3f8f7;
}

.heading {
  display: block;
  font-size: 40rpx;
  font-weight: 900;
  color: #0f5c56;
}

.filters {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  margin: 24rpx 0 28rpx;
}

.filter {
  padding: 14rpx 32rpx;
  border-radius: 999rpx;
  background: #fff;
  color: #4a6b67;
  font-size: 26rpx;
  font-weight: 600;
  border: 1rpx solid rgba(26, 95, 90, 0.12);
}

.filter.active {
  background: #1a7a72;
  color: #fff;
  border-color: #1a7a72;
}

.empty {
  margin-top: 80rpx;
  text-align: center;
  color: #8aa3a0;
  font-size: 28rpx;
}

.tile-gap {
  margin-bottom: 16rpx;
}
</style>
