import axios from 'axios'
import type { SearchRequest, AgentResponse } from '@/types'

// 后端API基础地址
// 开发环境通过 vite proxy 代理 /chat 到 localhost:8000
// 生产环境可通过 VITE_API_BASE_URL 配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30*60*1000, // 30分钟超时（Agent调用需要时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('📤 发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('❌ 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('❌ 响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成旅行计划/搜索景点美食/修改行程
 * 所有操作统一使用 /chat 端点
 */
export async function chatWithAgent(request: SearchRequest): Promise<AgentResponse> {
  try {
    const response = await apiClient.post<AgentResponse>('/chat', request)
    return response.data
  } catch (error: any) {
    console.error('Agent请求失败:', error)
    const detail = error.response?.data?.detail || error.message || '请求失败，请稍后重试'
    throw new Error(detail)
  }
}

/**
 * 生成唯一的会话ID
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * 生成用户ID（可从localStorage读取或新建）
 */
export function getUserId(): string {
  const stored = localStorage.getItem('travel_agent_user_id')
  if (stored) return stored
  const newId = import.meta.env.VITE_USER_ID || `user_${Date.now()}`
  localStorage.setItem('travel_agent_user_id', newId)
  return newId
}

export default apiClient
