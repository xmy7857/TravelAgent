<template>
  <div class="result-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <a-button class="back-button" size="large" @click="goBack">
        ← 返回首页
      </a-button>
      <div class="header-info" v-if="tripInfo">
        <span class="header-city">{{ tripInfo.city }}</span>
        <span class="header-date">{{ tripInfo.date_departure }} · {{ tripInfo.days }}天</span>
      </div>
      <a-space size="middle">
        <!-- 如果还没生成详细规划，显示此按钮 -->
        <a-button
          v-if="!hasTravelPlan && !loading"
          type="primary"
          size="large"
          @click="generateDetailedPlan"
          :loading="planGenerating"
        >
          📋 生成详细规划
        </a-button>
        <a-button
          v-if="hasTravelPlan"
          type="default"
          size="large"
          @click="clearPlan"
        >
          ↩️ 删除详细规划
        </a-button>
      </a-space>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !parsedData" class="loading-wrapper">
      <a-spin size="large" tip="AI Agent 正在处理中..." />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-wrapper">
      <a-result status="error" :title="error">
        <template #extra>
          <a-button type="primary" @click="goBack">返回首页</a-button>
        </template>
      </a-result>
    </div>

    <!-- 主内容 -->
    <div v-else class="content-wrapper">
      <!-- 左侧：结果展示区 -->
      <div class="main-content">
        <!-- Agent 说的额外话 -->
        <!-- <a-alert
          v-if="currentSaying"
          :message="currentSaying"
          type="info"
          show-icon
          closable
          class="saying-alert"
        /> -->

        <!-- 详细行程规划展示（放在最上方） -->
        <div v-if="travelPlan && hasTravelPlan">
          <a-card title="📅 详细行程规划" :bordered="false" class="section-card">
            <a-collapse v-model:activeKey="activeDays" accordion>
              <a-collapse-panel
                v-for="(day, index) in travelPlan.travel_plan"
                :key="index"
                :id="`day-${index}`"
              >
                <template #header>
                  <div class="day-header">
                    <span class="day-title">{{ day.day }}</span>
                    <a-tag color="purple">{{ day.theme }}</a-tag>
                  </div>
                </template>

                <div class="day-detail">
                  <!-- 路线 -->
                  <div class="day-route">
                    <div class="route-title">🗺️ 游玩路线</div>
                    <a-timeline>
                      <a-timeline-item
                        v-for="(stop, stopIdx) in day.route"
                        :key="stopIdx"
                        :color="stopIdx === 0 ? 'green' : stopIdx === day.route.length - 1 ? 'red' : 'blue'"
                      >
                        <template #dot v-if="stopIdx === 0">
                          <span style="font-size: 16px;">🚩</span>
                        </template>
                        <template #dot v-else-if="stopIdx === day.route.length - 1">
                          <span style="font-size: 16px;">🏁</span>
                        </template>
                        <span class="route-stop">{{ stop }}</span>
                      </a-timeline-item>
                    </a-timeline>
                  </div>

                  <!-- 描述 -->
                  <a-divider />
                  <div class="day-description">
                    <span class="desc-label">📝 行程说明：</span>
                    <p>{{ day.description }}</p>
                  </div>

                  <!-- 酒店信息 -->
                  <div v-if="day.hotel" class="day-hotel">
                    <a-divider />
                    <div class="hotel-info">
                      <span class="desc-label">🏨 推荐住宿：</span>
                      <span>{{ day.hotel.name }}</span>
                      <span v-if="day.hotel.address" style="color: #888; margin-left: 8px;">| {{ day.hotel.address }}</span>
                    </div>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </a-card>
        </div>

        <!-- 搜索结果展示：景点 + 美食（生成详细规划后也保留） -->
        <div v-if="searchResult">
          <!-- 景点列表 -->
          <a-card title="🎯 推荐景点" :bordered="false" class="section-card">
            <template #extra>
              <a-tag color="blue">{{ searchResult.attractions?.length || 0 }} 个景点</a-tag>
            </template>
            <a-list
              :data-source="searchResult.attractions"
              :grid="{ gutter: 16, column: 2 }"
            >
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-tooltip title="点击询问 AI 更多信息" placement="top">
                    <a-card
                      size="small"
                      class="attraction-card clickable-card"
                      :hoverable="true"
                      @click="askAbout(item.name)"
                    >
                      <div class="attr-card-body">
                        <div class="attr-content">
                          <div class="attr-header">
                            <span class="attr-name">{{ item.name }}</span>
                            <a-rate :value="item.score / 2" disabled allow-half :count="5" style="font-size: 14px;" />
                            <span class="attr-score">{{ item.score }}/10</span>
                          </div>
                          <p class="attr-reason">💡 {{ item.reason }}</p>
                          <p class="attr-time">⏱️ 建议游玩：{{ item.tour_time }} 小时</p>
                        </div>
                      </div>
                      <div class="click-hint">💬 询问详情</div>
                    </a-card>
                  </a-tooltip>
                </a-list-item>
              </template>
            </a-list>
            <a-empty v-if="!searchResult.attractions?.length" description="暂无景点推荐" />
          </a-card>

          <!-- 美食列表 -->
          <a-card title="🍜 推荐美食" :bordered="false" class="section-card" style="margin-top: 20px;">
            <template #extra>
              <a-tag color="orange">{{ searchResult.foods?.length || 0 }} 个美食</a-tag>
            </template>
            <a-list
              :data-source="searchResult.foods"
              :grid="{ gutter: 16, column: 2 }"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-tooltip title="点击询问 AI 更多信息" placement="top">
                    <a-card
                      size="small"
                      class="food-card clickable-card"
                      :hoverable="true"
                      @click="askAbout(item.name)"
                    >
                      <div class="food-header">
                        <span class="food-name">{{ item.name }}</span>
                        <a-tag :color="item.food_type === '主食' ? 'red' : 'orange'">
                          {{ item.food_type }}
                        </a-tag>
                      </div>
                      <div class="food-info">
                        <a-rate :value="item.score / 2" disabled allow-half :count="5" style="font-size: 12px;" />
                        <span class="food-score">{{ item.score }}/10</span>
                      </div>
                      <p class="food-reason">💡 {{ item.reason }}</p>
                      <p class="food-address" v-if="item.address">📍 {{ item.address }}</p>
                      <div class="click-hint">💬 询问详情</div>
                    </a-card>
                  </a-tooltip>
                </a-list-item>
              </template>
            </a-list>
            <a-empty v-if="!searchResult.foods?.length" description="暂无美食推荐" />
          </a-card>
        </div>

        <!-- 天气和车票信息（景点美食列表下方，纵向排列） -->
        <div v-if="weather || travelMode" class="weather-train-col">
          <!-- 天气：优先结构化卡片，解析失败则降级为纯文本 -->
          <a-card v-if="weather" title="🌤️ 天气情况" :bordered="false" class="info-card weather-card">
            <template v-if="weatherData">
              <div class="weather-city-tag">
                <a-tag color="blue">{{ weatherData.city }}</a-tag>
              </div>
              <div class="weather-cards-grid">
                <div
                  v-for="(day, idx) in weatherData.weather"
                  :key="idx"
                  class="weather-day-card"
                >
                  <div class="weather-day-header">
                    <span class="weather-date-text">📅 {{ day.date }}</span>
                    <span class="weather-condition">{{ day.condition }}</span>
                  </div>
                  <div class="weather-temp-row">
                    <span class="temp-high">🌡️ {{ day.max_temperature }}</span>
                    <span class="temp-sep">/</span>
                    <span class="temp-low">{{ day.min_temperature }}</span>
                  </div>
                  <div class="weather-wind">💨 {{ day['风力'] }}</div>
                  <div class="weather-advice">💡 {{ day.advice }}</div>
                </div>
              </div>
            </template>
            <div v-else class="info-content" v-html="renderedWeather"></div>
          </a-card>
          <!-- 火车票：优先结构化卡片，解析失败则降级为纯文本 -->
          <a-card v-if="travelMode" title="🚄 火车票推荐" :bordered="false" class="info-card train-card">
            <template v-if="trainData">
              <div class="train-cards-list">
                <div
                  v-for="(train, idx) in trainData.trains"
                  :key="idx"
                  class="train-item-card"
                >
                  <div class="train-top-row">
                    <span class="train-number-text">{{ train.train_number }}</span>
                    <span class="train-price">💳 {{ train.price }}</span>
                    <span class="train-seats">🎫 余票：{{ train.available_seats }}</span>
                  </div>
                  <div class="train-route-row">
                    <span class="station-name">{{ train.departure_station || '出发' }}</span>
                    <span class="station-time">{{ formatTrainTime(train.departure_time) }}</span>
                    <span class="train-duration">{{ train.duration }}h</span>
                    <span class="station-time">{{ formatTrainTime(train.arrival_time) }}</span>
                    <span class="station-name">{{ train.arrival_station || '到达' }}</span>
                  </div>
                  <div class="train-reason">💡 {{ train.reason }}</div>
                </div>
              </div>
            </template>
            <div v-else class="info-content" v-html="renderedTravelMode"></div>
          </a-card>
        </div>

      </div>

      <!-- 右侧：聊天面板 -->
      <div class="chat-panel">
        <a-card title="💬 与 AI 助手对话" :bordered="false" class="chat-card">
          <template #extra>
            <a-button size="small" @click="clearChat" :disabled="chatMessages.length <= 1">
              🗑️ 清空对话
            </a-button>
          </template>

          <!-- 消息列表 -->
          <div class="chat-messages" ref="chatContainer">
            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="chat-message"
              :class="`msg-${msg.role}`"
            >
              <div class="msg-avatar">
                {{ msg.role === 'user' ? '👤' : msg.role === 'assistant' ? '🤖' : '📢' }}
              </div>
              <div class="msg-bubble" :class="`bubble-${msg.role}`">
                <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
                <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>

            <!-- 加载指示器 -->
            <div v-if="chatLoading" class="chat-message msg-assistant">
              <div class="msg-avatar">🤖</div>
              <div class="msg-bubble bubble-assistant">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 快捷操作 -->
          <div class="quick-actions">
            <a-space wrap>
              <a-button size="small" @click="quickAction('帮我推荐更多景点')">🔍 更多景点</a-button>
              <a-button size="small" @click="quickAction('帮我推荐更多美食')">🍜 更多美食</a-button>
              <a-button size="small" @click="quickAction('移除评分较低的景点')">✂️ 精简景点</a-button>
            </a-space>
          </div>

          <!-- 输入区 -->
          <div class="chat-input-area">
            <a-textarea
              v-model:value="chatInput"
              :rows="2"
              placeholder="输入您的需求，例如：帮我加入更多博物馆类景点、去掉评分低于7分的项目..."
              @pressEnter="handleChatSend"
              :disabled="chatLoading"
            />
            <a-button
              type="primary"
              :loading="chatLoading"
              :disabled="!chatInput.trim()"
              @click="handleChatSend"
              class="send-button"
            >
              📤 发送
            </a-button>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { chatWithAgent, generateSessionId, getUserId } from '@/services/api'
import type {
  AgentResponse,
  SearchResult,
  TravelPlan,
  ModifyResponse,
  ChatMessage,
  SearchRequest,
  WeatherData,
  TrainData
} from '@/types'

const router = useRouter()

// ============ 基础状态 ============
const loading = ref(true)
const chatLoading = ref(false)
const planGenerating = ref(false)
const error = ref('')
const parsedData = ref<AgentResponse | null>(null)

// ============ 行程信息 ============
const tripInfo = ref<{ city: string; city_departure: string; date_departure: string; days: number } | null>(null)

// ============ 解析后的数据 ============
const searchResult = ref<SearchResult | null>(null)
const travelPlan = ref<TravelPlan | null>(null)
const currentSaying = ref('')
const hasTravelPlan = ref(false)

// ============ 天气和车票 ============
const weather = ref('')
const travelMode = ref('')

// ============ 聊天 ============
const chatInput = ref('')
const chatMessages = ref<ChatMessage[]>([])
const chatContainer = ref<HTMLElement | null>(null)
const activeDays = ref<number[]>([0])

// ============ 会话信息 ============
const userId = ref('')
const sessionId = ref('')
const lastSearchRequest = ref<SearchRequest | null>(null)

// ============ 计算属性 ============
/** 解析天气 JSON，失败则返回 null 降级为纯文本 */
const weatherData = computed<WeatherData | null>(() => {
  if (!weather.value) return null
  try {
    const jsonStr = extractJson(weather.value)
    const parsed = JSON.parse(jsonStr)
    if (parsed.weather && Array.isArray(parsed.weather)) {
      return parsed as WeatherData
    }
    return null
  } catch {
    return null
  }
})

const renderedWeather = computed(() => {
  if (!weather.value) return ''
  return marked.parse(weather.value) as string
})

/** 解析火车票 JSON，失败则返回 null 降级为纯文本 */
const trainData = computed<TrainData | null>(() => {
  if (!travelMode.value) return null
  try {
    const jsonStr = extractJson(travelMode.value)
    const parsed = JSON.parse(jsonStr)
    if (parsed.trains && Array.isArray(parsed.trains)) {
      return parsed as TrainData
    }
    return null
  } catch {
    return null
  }
})

const renderedTravelMode = computed(() => {
  if (!travelMode.value) return ''
  return marked.parse(travelMode.value) as string
})

// ============ 方法 ============

/**
 * 从文本中提取 JSON（支持 markdown 代码块包裹的情况）
 */
const extractJson = (text: string): string => {
  // 尝试匹配 ```json ... ``` 代码块
  const codeBlockMatch = text.match(/```json\s*([\s\S]*?)\s*```/)
  console.log("提取json代码块")
  if (codeBlockMatch) {
    console.log("匹配到json代码块")
    return codeBlockMatch[1].trim()
  }
  // 尝试匹配 ``` ... ``` 代码块（无语言标记）
  const genericBlockMatch = text.match(/```\s*([\s\S]*?)\s*```/)
  if (genericBlockMatch) {
    console.log("匹配到无语言标记代码块")
    return genericBlockMatch[1].trim()
  }
  return text.trim()
}

/**
 * 通过关键词 "travel_plan" 或 "attractions" 定位 JSON 并提取
 * 用于处理 LLM 在 JSON 前后输出了大量 markdown 文本但没包裹代码块的情况
 */
const extractJsonByKeyword = (text: string): string | null => {
  // 找到 "travel_plan" 或 "attractions" 关键字，向前找 {，向后匹配平衡 }
  for (const keyword of ['"travel_plan"', '"attractions"', '"foods"']) {
    console.log("找到关键字")
    const match = text.match(new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*:\\s*\\['))
    if (match && match.index !== undefined) {
      const before = text.substring(0, match.index)
      const openBraceIdx = before.lastIndexOf('{')
      if (openBraceIdx >= 0) {
        let depth = 0
        let endIdx = -1
        for (let i = openBraceIdx; i < text.length; i++) {
          if (text[i] === '{') depth++
          else if (text[i] === '}') {
            depth--
            if (depth === 0) { endIdx = i; break }
          }
        }
        if (endIdx > openBraceIdx) {
          return text.substring(openBraceIdx, endIdx + 1)
        }
      }
    }
  }
  return null
}

/** 多策略 JSON 解析，对 LLM 输出中的常见格式问题做容错 */
const tryParseJson = (jsonStr: string): any | null => {
  // 策略1: 直接解析
  try { return JSON.parse(jsonStr) } catch {}

  // 策略2: LLM 可能输出 Python dict（单引号），尝试替换为双引号
  if (jsonStr.trim().startsWith("{'") || /:\s*'/.test(jsonStr)) {
    try {
      // 将 key/value 中的单引号替换为双引号（注意字符串内部可能含转义）
      const fixed = jsonStr.replace(/'/g, '"')
      return JSON.parse(fixed)
    } catch {}
  }

  return null
}

/** 解析 Agent 返回的 ai_message */
const parseAiMessage = (aiMessage: string): { mainContent: any; saying: string } => {
  // 策略A: 从 markdown 代码块中提取 JSON
  const jsonStr = extractJson(aiMessage)
  let parsed = tryParseJson(jsonStr)

  if (parsed) {
    console.log('[parseAiMessage] 策略A(代码块) 解析成功')
  }

  // 策略B: 如果代码块提取失败，尝试通过关键词在原始文本中定位 JSON 结构
  if (!parsed) {
    const keywordJson = extractJsonByKeyword(aiMessage)
    if (keywordJson) {
      parsed = tryParseJson(keywordJson)
      if (parsed) {
        console.log('[parseAiMessage] 策略B(关键词定位) 解析成功')
      }
    }
  }

  // 策略C: 直接在原始 aiMessage 中搜索 JSON 结构（不依赖代码块）
  if (!parsed) {
    parsed = tryParseJson(aiMessage)
    if (parsed) {
      console.log('[parseAiMessage] 策略C(原始文本) 解析成功')
    }
  }

  // 所有策略都失败，回退为纯文本 saying
  if (!parsed) {
    console.warn('[parseAiMessage] 所有解析策略均失败，前200字:', aiMessage.substring(0, 200))
    return { mainContent: null, saying: aiMessage }
  }

  // 1. 判断是否是 TravelPlan：有 travel_plan 字段
  if (parsed.travel_plan !== undefined) {
    return {
      mainContent: parsed as TravelPlan,
      saying: parsed.saying || ''
    }
  }

  // 2. 判断是否是 SearchResult：有 attractions 或 foods 字段
  if (parsed.attractions !== undefined || parsed.foods !== undefined) {
    return {
      mainContent: parsed as SearchResult,
      saying: parsed.saying || ''
    }
  }

  // 3. 判断是否是 ModifyResponse 格式：有 main_content 字段
  if (parsed.main_content !== undefined) {
    let innerContent = parsed.main_content
    if (typeof innerContent === 'string') {
      const innerResult = parseAiMessage(innerContent)
      return {
        mainContent: innerResult.mainContent,
        saying: parsed.saying || innerResult.saying || ''
      }
    }
    return { mainContent: innerContent, saying: parsed.saying || '' }
  }

  // 4. 纯 saying
  if (parsed.saying !== undefined) {
    return { mainContent: null, saying: parsed.saying }
  }

  // 5. 无法识别，整个当作 saying
  return { mainContent: null, saying: aiMessage }
}

/** 根据 mainContent 更新页面状态 */
const applyMainContent = (mainContent: any, saying: string) => {
  currentSaying.value = saying

  if (!mainContent) return

  // 判断是 SearchResult 还是 TravelPlan
  if (mainContent.travel_plan) {
    // 这是 TravelPlan
    travelPlan.value = mainContent as TravelPlan
    hasTravelPlan.value = true
    // 同时也更新 searchResult（如果其中有 city/days 等信息）
    if (mainContent.city) {
      searchResult.value = mainContent as SearchResult
    }
  } else if (mainContent.attractions !== undefined || mainContent.foods !== undefined) {
    // 这是 SearchResult
    searchResult.value = mainContent as SearchResult
    hasTravelPlan.value = false
    travelPlan.value = null
  }
}

/** 处理 AgentResponse */
const handleAgentResponse = (response: AgentResponse, userMessage?: string) => {
  parsedData.value = response

  // 更新天气和车票
  if (response.weather) {
    weather.value = response.weather
  }
  if (response.travel_mode) {
    travelMode.value = response.travel_mode
  }

  // 解析 ai_message
  const { mainContent, saying } = parseAiMessage(response.ai_message)
  applyMainContent(mainContent, saying)

  // 添加到聊天记录
  if (saying) {
    chatMessages.value.push({
      role: 'assistant',
      content: saying,
      timestamp: Date.now(),
      type: hasTravelPlan.value ? 'travel_plan' : 'search_result'
    })
  } else if (mainContent) {
    const summary = hasTravelPlan.value
      ? `已生成 ${travelPlan.value?.travel_plan?.length || 0} 天的详细行程规划，请查看左侧面板。`
      : `已为您找到 ${searchResult.value?.attractions?.length || 0} 个景点和 ${searchResult.value?.foods?.length || 0} 个美食推荐。`
    chatMessages.value.push({
      role: 'assistant',
      content: summary,
      timestamp: Date.now(),
      type: hasTravelPlan.value ? 'travel_plan' : 'search_result'
    })
  }
}

/** 发送聊天消息 */
const handleChatSend = async () => {
  const input = chatInput.value.trim()
  if (!input || chatLoading.value) return

  chatInput.value = ''

  // 添加用户消息
  chatMessages.value.push({
    role: 'user',
    content: input,
    timestamp: Date.now()
  })

  chatLoading.value = true
  await scrollToBottom()

  try {
    const requestData: SearchRequest = {
      user_id: userId.value,
      session_id: sessionId.value,
      city_departure: lastSearchRequest.value?.city_departure || '',
      date_departure: lastSearchRequest.value?.date_departure || '',
      city: lastSearchRequest.value?.city || '',
      days: lastSearchRequest.value?.days || 1,
      user_prompt: input
    }

    const response = await chatWithAgent(requestData)
    handleAgentResponse(response, input)
  } catch (err: any) {
    message.error(err.message || '请求失败')
    chatMessages.value.push({
      role: 'assistant',
      content: '抱歉，请求处理失败，请稍后重试。',
      timestamp: Date.now()
    })
  } finally {
    chatLoading.value = false
    await scrollToBottom()
  }
}

/** 点击景点/美食卡片，填充聊天框 */
const askAbout = (name: string) => {
  chatInput.value = `请帮我详细介绍一下「${name}」，包括它的特色、历史背景、游玩攻略等。`
  // 滚动到聊天输入框
  const chatPanel = document.querySelector('.chat-input-area')
  if (chatPanel) {
    chatPanel.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }
  message.info(`已添加「${name}」到聊天框，点击发送即可询问 AI`)
}

/** 快捷操作 */
const quickAction = (action: string) => {
  chatInput.value = action
  handleChatSend()
}

/** 生成详细规划 */
const generateDetailedPlan = async () => {
  planGenerating.value = true
  const prompt = '我很满意当前的景点与美食。请根据我当前的景点和美食列表，帮我生成一份详细的每日行程规划，包括每天的游玩路线、交通方式、住宿建议和餐饮安排。返回JSON'

  chatMessages.value.push({
    role: 'user',
    content: '📋 请求生成详细行程规划',
    timestamp: Date.now()
  })

  chatLoading.value = true

  try {
    const requestData: SearchRequest = {
      user_id: userId.value,
      session_id: sessionId.value,
      city_departure: lastSearchRequest.value?.city_departure || '',
      date_departure: lastSearchRequest.value?.date_departure || '',
      city: lastSearchRequest.value?.city || '',
      days: lastSearchRequest.value?.days || 1,
      user_prompt: prompt
    }

    const response = await chatWithAgent(requestData)
    handleAgentResponse(response, prompt)

    message.success('详细规划已生成！')
  } catch (err: any) {
    message.error(err.message || '生成详细规划失败')
  } finally {
    planGenerating.value = false
    chatLoading.value = false
    await scrollToBottom()
  }
}

/** 清空详细规划，回到景点列表 */
const clearPlan = () => {
  hasTravelPlan.value = false
  travelPlan.value = null
  message.info('已删除详细规划')
}

/** 清空聊天记录 */
const clearChat = () => {
  chatMessages.value = []
  message.success('聊天记录已清空')
}

/** 滚动到底部 */
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

/** 从完整时间字符串中提取 HH:MM */
const formatTrainTime = (datetime: string): string => {
  const parts = datetime.split(' ')
  return parts.length > 1 ? parts[1].substring(0, 5) : datetime
}

/** 使用 marked 库渲染完整的 Markdown 语法 */
const renderMarkdown = (text: string): string => {
  return marked.parse(text) as string
}

/** 格式化时间 */
const formatTime = (ts: number): string => {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

/** 返回首页 */
const goBack = () => {
  router.push('/')
}

// ============ 生命周期 ============
onMounted(() => {
  // 从 sessionStorage 加载数据
  const storedResponse = sessionStorage.getItem('agentResponse')
  const storedSessionId = sessionStorage.getItem('currentSessionId')
  const storedUserId = sessionStorage.getItem('currentUserId')
  const storedRequest = sessionStorage.getItem('searchRequest')

  if (!storedResponse) {
    error.value = '未找到旅行计划数据，请返回首页开始搜索。'
    loading.value = false
    return
  }

  try {
    const response: AgentResponse = JSON.parse(storedResponse)
    sessionId.value = storedSessionId || response.session_id
    userId.value = storedUserId || response.user_id

    if (storedRequest) {
      lastSearchRequest.value = JSON.parse(storedRequest) as any
      tripInfo.value = JSON.parse(storedRequest)
    }

    // 添加欢迎消息
    chatMessages.value.push({
      role: 'system',
      content: `欢迎来到 ${tripInfo.value?.city || '目的地'}！AI Agent 已为您搜索了景点、美食、天气和火车票信息。您可以：\n• 在下方输入框发送修改需求\n• 点击快捷按钮进行常见操作\n• 点击「生成详细规划」获取每日行程`,
      timestamp: Date.now()
    })

    handleAgentResponse(response)
  } catch (e: any) {
    error.value = `数据解析失败: ${e.message}`
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.result-container {
  min-height: calc(100vh - 64px - 70px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 24px 24px;
}

/* 页面头部 */
.page-header {
  max-width: 1600px;
  margin: 0 auto 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInDown 0.6s ease-out;
}

.back-button {
  border-radius: 8px;
  font-weight: 500;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-city {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.header-date {
  font-size: 16px;
  color: #666;
  background: white;
  padding: 6px 16px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 加载/错误包装 */
.loading-wrapper,
.error-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

/* 内容布局 */
.content-wrapper {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.main-content {
  flex: 6;
  min-width: 0;
}

/* 天气/车票：纵向排列，位于景点美食下方 */
.weather-train-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
  animation: fadeInUp 0.6s ease-out;
}

.weather-train-col .info-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.weather-train-col .weather-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #42a5f5 0%, #1e88e5 100%);
  border-radius: 12px 12px 0 0;
}

.weather-train-col .weather-card :deep(.ant-card-head-title) {
  color: white !important;
  font-size: 15px;
}

.weather-train-col .train-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #66bb6a 0%, #43a047 100%);
  border-radius: 12px 12px 0 0;
}

.weather-train-col .train-card :deep(.ant-card-head-title) {
  color: white !important;
  font-size: 15px;
}

.weather-train-col .info-content {
  font-size: 13px;
  line-height: 1.7;
  color: #444;
}

/* 结构化天气卡片网格 */
.weather-city-tag {
  margin-bottom: 12px;
}

.weather-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.weather-day-card {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #90caf9;
  transition: all 0.25s ease;
}

.weather-day-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 165, 245, 0.25);
}

.weather-day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(66, 165, 245, 0.2);
}

.weather-date-text {
  font-size: 14px;
  font-weight: 600;
  color: #1565c0;
}

.weather-condition {
  font-size: 15px;
  font-weight: 700;
  color: #0d47a1;
}

.weather-temp-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 6px;
}

.temp-high {
  font-size: 20px;
  font-weight: 700;
  color: #e53935;
}

.temp-sep {
  font-size: 14px;
  color: #999;
}

.temp-low {
  font-size: 16px;
  font-weight: 600;
  color: #1e88e5;
}

.weather-wind {
  font-size: 12px;
  color: #546e7a;
  margin-bottom: 8px;
}

.weather-advice {
  font-size: 12px;
  color: #37474f;
  line-height: 1.5;
  padding-top: 6px;
  border-top: 1px dashed rgba(66, 165, 245, 0.2);
}

/* 结构化火车票卡片列表 */
.train-cards-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.train-item-card {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid #a5d6a7;
  transition: all 0.25s ease;
}

.train-item-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(76, 175, 80, 0.2);
}

.train-top-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.train-number-text {
  font-size: 22px;
  font-weight: 800;
  color: #2e7d32;
  letter-spacing: 1px;
  margin-right: auto;
}

.train-price {
  color: #e65100;
  font-weight: 600;
  font-size: 13px;
}

.train-seats {
  color: #2e7d32;
  font-weight: 500;
  font-size: 13px;
}

.train-route-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.station-name {
  font-size: 14px;
  color: #2e7d32;
  font-weight: 600;
}

.station-time {
  font-size: 14px;
  font-weight: 700;
  color: #333;
}

.train-duration {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #2e7d32;
  background: linear-gradient(to right, #c8e6c9, #e8f5e9, #c8e6c9);
  padding: 2px 12px;
  border-radius: 10px;
  white-space: nowrap;
}

.train-reason {
  font-size: 12px;
  color: #555;
  padding-top: 4px;
  border-top: 1px dashed rgba(76, 175, 80, 0.25);
  line-height: 1.4;
}

/* Saying 提示 */
.saying-alert {
  margin-bottom: 16px;
  border-radius: 12px;
  animation: fadeInUp 0.6s ease-out;
}

/* 区域卡片 */
.section-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  animation: fadeInUp 0.6s ease-out;
}

.section-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-radius: 12px 12px 0 0;
}

.section-card :deep(.ant-card-head-title) {
  color: white !important;
  font-size: 18px;
}

/* 景点卡片 */
.attraction-card {
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.attraction-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

/* 可点击卡片通用样式 */
.clickable-card {
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.clickable-card .click-hint {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  opacity: 0;
  transform: translateY(-4px);
  transition: all 0.25s ease;
  pointer-events: none;
}

.clickable-card:hover .click-hint {
  opacity: 1;
  transform: translateY(0);
}

.attr-card-body {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.attr-content {
  flex: 1;
  min-width: 0;
}

.attr-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.attr-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.attr-score {
  font-size: 13px;
  color: #faad14;
  font-weight: 500;
}

.attr-reason {
  color: #555;
  margin: 4px 0;
  font-size: 13px;
}

.attr-time {
  color: #888;
  font-size: 12px;
  margin: 0;
}

/* 美食卡片 */
.food-card {
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.food-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.food-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.food-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.food-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.food-score {
  font-size: 13px;
  color: #faad14;
  font-weight: 500;
}

.food-reason {
  color: #555;
  margin: 4px 0;
  font-size: 13px;
}

.food-address {
  color: #888;
  font-size: 12px;
  margin: 0;
}

/* 每日行程 */
.day-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.day-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.day-detail {
  padding: 8px 0;
}

.day-route {
  margin-bottom: 8px;
}

.route-title {
  font-weight: 600;
  color: #555;
  margin-bottom: 12px;
}

.route-stop {
  font-size: 15px;
  color: #333;
}

.day-description p {
  color: #555;
  line-height: 1.8;
  margin: 8px 0 0 0;
}

.desc-label {
  font-weight: 600;
  color: #555;
}

.hotel-info {
  font-size: 14px;
  color: #333;
}

/* 聊天面板 */
.chat-panel {
  flex: 4;
  min-width: 320px;
  position: sticky;
  top: 24px;
}

.chat-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-radius: 12px 12px 0 0;
}

.chat-card :deep(.ant-card-head-title) {
  color: white !important;
}

.chat-card :deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  max-height: 100%;
}

.chat-message {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #f0f0f0;
}

.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.bubble-user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.bubble-assistant {
  background: #f0f2f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.bubble-system {
  background: #e6f7ff;
  color: #333;
  border: 1px dashed #91d5ff;
  border-radius: 12px;
  font-size: 13px;
}

.msg-content {
  margin-bottom: 4px;
}

.msg-time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
  text-align: right;
}

.msg-user .msg-time {
  color: rgba(255, 255, 255, 0.7);
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #bbb;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.6;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* 快捷操作 */
.quick-actions {
  padding: 10px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  margin: 8px 0;
}

/* 聊天输入 */
.chat-input-area {
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.chat-input-area :deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  resize: none;
}

.chat-input-area :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.send-button {
  margin-top: 8px;
  width: 100%;
  border-radius: 20px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Collapse 样式 */
:deep(.ant-collapse) {
  border: none;
  background: transparent;
}

:deep(.ant-collapse-item) {
  margin-bottom: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}

:deep(.ant-collapse-header) {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  padding: 14px 20px !important;
  font-weight: 600;
}

:deep(.ant-collapse-content) {
  border-top: 1px solid #e8e8e8;
}

:deep(.ant-collapse-content-box) {
  padding: 20px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .content-wrapper {
    flex-direction: column;
  }
  .chat-panel {
    flex: auto;
    width: 100%;
    position: static;
  }
  .chat-card {
    height: 500px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
  }
  .result-container {
    padding: 16px 10px;
  }
}
</style>
