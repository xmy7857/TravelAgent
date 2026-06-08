// ============================================================
// 类型定义 - 与后端 schemas.py 对应
// ============================================================

/** 景点条目 */
export interface AttrItem {
  name: string
  score: number
  reason: string
  tour_time: number
}

/** 美食条目 */
export interface FoodItem {
  name: string
  food_type: string  // '主食' 或 '小吃'
  score: number
  reason: string
  address: string
}

/** 搜索结果（景点+美食列表） */
export interface SearchResult {
  city: string
  days: number
  attractions: AttrItem[]
  foods: FoodItem[]
  saying?: string
}

/** 单日行程 */
export interface TravelDay {
  day: string
  theme: string
  route: string[]
  hotel?: {
    name: string
    address: string
  }
  description: string
}

/** 完整旅行计划 */
export interface TravelPlan {
  travel_plan: TravelDay[]
  saying?: string
}

/** 修改返回格式 */
export interface ModifyResponse {
  main_content: SearchResult | TravelPlan | null
  saying: string
}

/** 发送给后端的搜索请求 */
export interface SearchRequest {
  user_id: string
  session_id: string
  city_departure: string
  date_departure: string
  city: string
  days: number
  user_prompt: string
}

/** 后端返回的 Agent 响应 */
export interface AgentResponse {
  user_id: string
  session_id: string
  ai_message: string   // JSON字符串，需解析
  weather: string
  travel_mode: string
}

/** 旅行风格标签 */
export interface PreferenceTag {
  key: string
  label: string
  icon: string
}

/** 消息类型（用于聊天界面） */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  type?: 'text' | 'search_result' | 'travel_plan' | 'weather' | 'train'
}

/** 天气单日数据 */
export interface WeatherDay {
  date: string
  condition: string
  max_temperature: string
  min_temperature: string
  '风力': string
  advice: string
}

/** 天气查询返回格式 */
export interface WeatherData {
  city: string
  weather: WeatherDay[]
}

/** 单趟列车信息 */
export interface TrainItem {
  train_number: string
  departure_station: string
  arrival_station: string
  departure_time: string
  arrival_time: string
  duration: number
  price: string
  available_seats: string
  reason: string
}

/** 火车票查询返回格式 */
export interface TrainData {
  trains: TrainItem[]
}

/** 当前页面状态 */
export type PageState = 'search_result' | 'travel_plan' | 'loading' | 'error'
