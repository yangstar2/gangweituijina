<template>
  <view class="page">
    <view class="hero" :style="{ paddingTop: statusBarPx + 'px' }">
      <text class="brand">AI 个人提醒助手</text>
      <text class="greeting">{{ greet }}，想提醒什么？</text>

      <view class="input-card">
        <textarea
          v-model="nlText"
          class="nl-input"
          :disabled="parsing"
          maxlength="200"
          auto-height
          placeholder="例如：明天下午四点半提醒我交数学作业"
          placeholder-class="nl-placeholder"
        />
        <button class="primary-btn" :loading="parsing" :disabled="parsing" @click="() => onParse()">
          {{ parsing ? '解析中…' : 'AI 解析' }}
        </button>
      </view>

      <view class="shortcuts">
        <view class="chip" @click="onTenMinutes">10 分钟后</view>
        <view class="chip outline" @click="onPickTime">指定时间</view>
      </view>
    </view>

    <view class="sections">
      <view class="section-head">
        <text class="section-title">今日待办</text>
        <text class="section-count">{{ today.length }}</text>
      </view>
      <view v-if="!today.length" class="empty">今天还没有待办，说一句话创建吧</view>
      <ReminderTile v-for="r in today" :key="r.id" class="tile-gap" :reminder="r" />

      <view class="section-head">
        <text class="section-title">即将提醒</text>
        <text class="section-count">{{ upcoming.length }}</text>
      </view>
      <view v-if="!upcoming.length" class="empty">近期没有安排</view>
      <ReminderTile
        v-for="r in upcoming.slice(0, 5)"
        :key="r.id"
        class="tile-gap"
        :reminder="r"
      />

      <view class="section-head">
        <text class="section-title">已完成</text>
        <text class="section-count">{{ done.length }}</text>
      </view>
      <view v-if="!done.length" class="empty">完成的提醒会出现在这里</view>
      <ReminderTile
        v-for="r in done.slice(0, 3)"
        :key="r.id"
        class="tile-gap"
        :reminder="r"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ReminderTile from '../../components/ReminderTile.vue'
import { parseNaturalLanguage } from '../../services/mockAiParser'
import { reminderStore, useReminderLists } from '../../store/reminders'
import { greeting } from '../../utils/dateFormatZh'

const { today, upcoming, done } = useReminderLists()
const nlText = ref('')
const parsing = ref(false)
const greet = greeting()
const statusBarPx = uni.getSystemInfoSync().statusBarHeight || 20

async function onParse(override?: string) {
  const text = (override ?? nlText.value).trim()
  if (!text) {
    uni.showToast({ title: '先说一句想提醒的事吧～', icon: 'none' })
    return
  }
  parsing.value = true
  try {
    const draft = await parseNaturalLanguage(text)
    reminderStore.setDraft(draft)
    uni.navigateTo({ url: '/pages/confirm/index' })
    if (!override) nlText.value = ''
  } finally {
    parsing.value = false
  }
}

function onTenMinutes() {
  const text = '10 分钟后提醒我休息一下'
  nlText.value = text
  onParse(text)
}

function onPickTime() {
  const due = new Date(Date.now() + 60 * 60 * 1000)
  reminderStore.setDraft(
    {
      title: '',
      dueAt: due.toISOString(),
      repeatType: 'none',
      repeatDays: [],
    },
    '指定时间',
  )
  uni.navigateTo({ url: '/pages/settings/index?mode=create' })
}
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: #f3f8f7;
}

.hero {
  padding: 24rpx 40rpx 28rpx;
  background: linear-gradient(145deg, #c8e8e4 0%, #e8f3ef 55%, #f3f8f7 100%);
}

.brand {
  display: block;
  font-size: 44rpx;
  font-weight: 900;
  color: #0f5c56;
  letter-spacing: 1rpx;
}

.greeting {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  color: #4a6b67;
}

.input-card {
  margin-top: 28rpx;
  padding: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 24rpx;
  border: 1rpx solid rgba(15, 92, 86, 0.1);
}

.nl-input {
  width: 100%;
  min-height: 120rpx;
  font-size: 30rpx;
  color: #1a3a38;
  line-height: 1.5;
}

.nl-placeholder {
  color: #9bb0ad;
}

.primary-btn {
  margin-top: 20rpx;
  background: #1a7a72;
  color: #fff;
  border-radius: 16rpx;
  font-size: 30rpx;
  font-weight: 700;
  border: none;
}

.primary-btn[disabled] {
  opacity: 0.7;
}

.shortcuts {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  margin-top: 20rpx;
}

.chip {
  padding: 14rpx 28rpx;
  background: #1a7a72;
  color: #fff;
  border-radius: 999rpx;
  font-size: 26rpx;
  font-weight: 600;
}

.chip.outline {
  background: rgba(255, 255, 255, 0.85);
  color: #1a7a72;
  border: 1rpx solid rgba(26, 122, 114, 0.35);
}

.sections {
  padding: 16rpx 40rpx 48rpx;
}

.section-head {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 12rpx;
  margin: 28rpx 0 16rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #0f5c56;
}

.section-count {
  font-size: 24rpx;
  color: #6b8582;
}

.empty {
  padding: 12rpx 8rpx 8rpx;
  font-size: 26rpx;
  color: #8aa3a0;
}

.tile-gap {
  margin-bottom: 16rpx;
}
</style>
