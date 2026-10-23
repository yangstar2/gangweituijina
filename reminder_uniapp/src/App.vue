<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('[AI 个人提醒助手] App Launch — Stage 01 UI (in-memory)')
})
onShow(() => {
  console.log('[AI 个人提醒助手] App Show')
})
onHide(() => {
  console.log('[AI 个人提醒助手] App Hide')
})
</script>

<style lang="scss">
page {
  background-color: #f3f8f7;
  color: #1a3a38;
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', 'Microsoft YaHei',
    sans-serif;
}
</style>
