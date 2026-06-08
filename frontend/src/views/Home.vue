<template>
  <div class="home-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <!-- 页面标题 -->
    <div class="page-header">
      <div class="icon-wrapper">
        <span class="icon">✈️</span>
      </div>
      <h1 class="page-title">智能旅行助手</h1>
      <p class="page-subtitle">基于AI Agent的个性化旅行规划，搜索景点美食、查询天气车票、生成详细行程</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <!-- 第一步：目的地与日期 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">📍</span>
            <span class="section-title">目的地与行程</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>
                  <span class="form-label">🏙️ 目的地城市</span>
                </template>
                <a-input
                  v-model:value="formData.city"
                  placeholder="例如：北京、南京、成都..."
                  size="large"
                  class="custom-input"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="city_departure" :rules="[{ required: true, message: '请输入出发城市' }]">
                <template #label>
                  <span class="form-label">🚄 出发城市</span>
                </template>
                <a-input
                  v-model:value="formData.city_departure"
                  placeholder="例如：上海、广州..."
                  size="large"
                  class="custom-input"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item name="date_departure" :rules="[{ required: true, message: '请选择出发日期' }]">
                <template #label>
                  <span class="form-label">📅 出发日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.date_departure"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                  :disabled-date="disabledDate"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item name="days" :rules="[{ required: true, message: '请选择游玩天数' }]">
                <template #label>
                  <span class="form-label">📆 游玩天数</span>
                </template>
                <a-select v-model:value="formData.days" size="large" class="custom-select">
                  <a-select-option v-for="d in 15" :key="d" :value="d">{{ d }} 天</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第二步：旅行偏好 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">🎯</span>
            <span class="section-title">旅行偏好（可选）</span>
          </div>

          <a-form-item name="preferences">
            <div class="preference-tags">
              <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                <a-checkbox value="历史文化" class="preference-tag">🏛️ 历史文化</a-checkbox>
                <a-checkbox value="自然风光" class="preference-tag">🏞️ 自然风光</a-checkbox>
                <a-checkbox value="美食探店" class="preference-tag">🍜 美食探店</a-checkbox>
                <a-checkbox value="购物消费" class="preference-tag">🛍️ 购物消费</a-checkbox>
                <a-checkbox value="艺术展览" class="preference-tag">🎨 艺术展览</a-checkbox>
                <a-checkbox value="休闲度假" class="preference-tag">☕ 休闲度假</a-checkbox>
                <a-checkbox value="亲子游玩" class="preference-tag">👨‍👩‍👧 亲子游玩</a-checkbox>
                <a-checkbox value="探险户外" class="preference-tag">🧗 探险户外</a-checkbox>
              </a-checkbox-group>
            </div>
          </a-form-item>
        </div>

        <!-- 第三步：额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">额外要求（可选）</span>
          </div>

          <a-form-item name="user_prompt">
            <a-textarea
              v-model:value="formData.user_prompt"
              placeholder="请输入您的额外要求，例如：想去看升旗仪式、对海鲜过敏、需要无障碍设施、偏好小众景点..."
              :rows="3"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        <!-- 提交按钮 -->
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            size="large"
            block
            class="submit-button"
          >
            <template v-if="!loading">
              <span class="button-icon">🚀</span>
              <span>生成旅行计划</span>
            </template>
            <template v-else>
              <span>AI Agent 正在工作中...</span>
            </template>
          </a-button>
        </a-form-item>

        <!-- 加载进度提示 -->
        <a-form-item v-if="loading">
          <div class="loading-container">
            <a-progress
              :percent="loadingProgress"
              status="active"
              :stroke-color="{
                '0%': '#667eea',
                '100%': '#764ba2',
              }"
              :stroke-width="10"
              :show-info="false"
            />
            <p class="loading-status">{{ loadingStatus }}</p>
          </div>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs, { type Dayjs } from 'dayjs'
import { chatWithAgent, generateSessionId, getUserId } from '@/services/api'
import type { SearchRequest } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

// 表单数据
const formData = reactive({
  city: '',
  city_departure: '',
  date_departure: null as Dayjs | null,
  days: 3,
  preferences: [] as string[],
  user_prompt: ''
})

// 禁用今天之前的日期
const disabledDate = (current: Dayjs) => {
  return current && current.isBefore(dayjs().subtract(1, 'day'))
}

// 构建用户提示词
const buildUserPrompt = (): string => {
  const parts: string[] = []
  if (formData.preferences.length > 0) {
    parts.push(`旅行偏好：${formData.preferences.join('、')}`)
  }
  if (formData.user_prompt.trim()) {
    parts.push(`额外要求：${formData.user_prompt.trim()}`)
  }
  return parts.join('。')
}

const handleSubmit = async () => {
  if (!formData.date_departure) {
    message.error('请选择出发日期')
    return
  }

  if (!formData.city || !formData.city_departure) {
    message.error('请填写目的地城市和出发城市')
    return
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = '🔍 正在初始化...'

  // 模拟进度更新
  const stages = [
    { progress: 15, status: '🔍 Agent 正在搜索景点和美食...' },
    { progress: 35, status: '🌤️ Agent 正在查询天气信息...' },
    { progress: 55, status: '🚄 Agent 正在查询火车票信息...' },
    { progress: 75, status: '📋 Agent 正在综合分析生成结果...' },
    { progress: 90, status: '📦 正在整理返回数据...' },
  ]

  let stageIndex = 0
  const progressInterval = setInterval(() => {
    if (stageIndex < stages.length && loadingProgress.value < 90) {
      const stage = stages[stageIndex]
      loadingProgress.value = stage.progress
      loadingStatus.value = stage.status
      stageIndex++
    }
  }, 1500)

  try {
    const requestData: SearchRequest = {
      user_id: getUserId(),
      session_id: generateSessionId(),
      city_departure: formData.city_departure,
      date_departure: formData.date_departure.format('YYYY-MM-DD'),
      city: formData.city,
      days: formData.days,
      user_prompt: buildUserPrompt()
    }

    const response = await chatWithAgent(requestData)

    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成！'

    // 保存到 sessionStorage 供 Result 页面使用
    sessionStorage.setItem('agentResponse', JSON.stringify(response))
    sessionStorage.setItem('currentSessionId', requestData.session_id)
    sessionStorage.setItem('currentUserId', requestData.user_id)
    // 保存原始请求信息
    sessionStorage.setItem('searchRequest', JSON.stringify({
      city: requestData.city,
      city_departure: requestData.city_departure,
      date_departure: requestData.date_departure,
      days: requestData.days
    }))

    message.success('搜索完成！')

    // 短暂延迟后跳转
    setTimeout(() => {
      router.push('/result')
    }, 500)
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '请求失败，请稍后重试')
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 1000)
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: 30%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
  }
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 50px;
  animation: fadeInDown 0.8s ease-out;
  position: relative;
  z-index: 1;
}

.icon-wrapper {
  margin-bottom: 20px;
}

.icon {
  font-size: 80px;
  display: inline-block;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.page-title {
  font-size: 56px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 16px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
  letter-spacing: 2px;
}

.page-subtitle {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  font-weight: 300;
}

/* 表单卡片 */
.form-card {
  max-width: 1100px;
  margin: 0 auto;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98) !important;
}

/* 表单分区 */
.form-section {
  margin-bottom: 28px;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #667eea;
}

.section-icon {
  font-size: 24px;
  margin-right: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 表单标签 */
.form-label {
  font-size: 15px;
  font-weight: 500;
  color: #555;
}

/* 自定义输入框 */
.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 自定义选择框 */
.custom-select :deep(.ant-select-selector) {
  border-radius: 12px !important;
  border: 2px solid #e8e8e8 !important;
  transition: all 0.3s ease;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: #667eea !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* 偏好标签 */
.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.preference-tag :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 20px;
  transition: all 0.3s ease;
  background: white;
  font-size: 14px;
}

.preference-tag :deep(.ant-checkbox-wrapper:hover) {
  border-color: #667eea;
  background: #f5f7ff;
}

.preference-tag :deep(.ant-checkbox-wrapper-checked) {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 自定义文本域 */
.custom-textarea :deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #667eea;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 提交按钮 */
.submit-button {
  height: 56px;
  border-radius: 28px;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.submit-button:active {
  transform: translateY(0);
}

.button-icon {
  margin-right: 8px;
  font-size: 20px;
}

/* 加载容器 */
.loading-container {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 2px dashed #667eea;
}

.loading-status {
  margin-top: 16px;
  color: #667eea;
  font-size: 18px;
  font-weight: 500;
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .page-title {
    font-size: 36px;
  }
  .page-subtitle {
    font-size: 16px;
  }
  .form-card {
    margin: 0 10px;
  }
}
</style>
