
## 使用指南
1. 在首页填写旅行信息:
   - 目的地城市
   - 出发的城市
   - 出发日期和旅行天数
   - 旅行风格标签
   - 其他偏好

2. 点击"生成旅行计划"按钮，以JSON报文发送给客户端，报文格式见**发送报文**

3. 系统将:
   - 调用Agent为用户搜索景点和美食
   - Agent获取天气信息
   - Agent调用12306-mcp查询火车票
   - 以JSON报文格式返回，返回格式见**搜索返回报文**

4. 用户向Agent发送信息，要求其修改景点与美食列表，或点击“生成详细规划按钮”以生成详细的旅行线路规划。
   - 如果用户要求修改景点与美食列表，返回报文格式见**修改返回报文**
   - 如果用户点击了“生成详细规划”按钮，返回报文格式见**详细规划返回报文**

5. 查看结果:
   - 每日详细行程
   - 天气预报
   - 火车票信息
6. 修改详细行程规划
   - 如果用户要求修改详细行程规划，返回报文格式见**修改返回报文**

**发送报文**
```
class SearchRequest(BaseModel):
    user_id: str = Field(...,description="用户编号")
    session_id: str = Field(...,description="会话编号")
    city_departure: str = Field(...,description="出发城市")
    date_departure: str = Field(...,description="出发日期")
    city: str = Field(...,description="用户计划到达的城市")
    days: int = Field(...,description="用户计划游玩的天数")
    user_prompt: str = Field(description="用户要求",default="")
```

**搜索返回报文**
```
class AgentResponse(BaseModel):
    user_id: str = Field(...,description="用户编号")
    session_id: str = Field(...,description="会话编号")
    ai_message: SearchResult = Field(...,description="用户消息")
    weather: str = Field(default="",description="天气情况")
    travel_mode: str = Field(default="",description="推荐的列车车次列表")
class SearchResult(BaseModel):
    city: str = Field(...,description="用户计划出行的城市")
    days: int = Field(...,description="用户计划游玩的天数")
    attractions: list[AttrItem] = Field(...,description="景点列表")
    foods: list[FoodItem] = Field(...,description="美食列表")
    saying: str = Feild(default="",description="Agent额外对用户说的话")
class AttrItem(BaseModel):
    name: str = Field(...,description="景点名称")
    score: int = Field(...,le=1, ge=10,description="评分")
    reason: str = Field(...,description="简短的推荐理由")
    tour_time: float = Field(...,le=0.0,description="游玩时间(小时)")

class FoodItem(BaseModel):
    name: str = Field(...,description="美食名称")
    food_type: str = Field(...,description="美食类型，填'主食'或'小吃'")
    score: int = Field(...,le=1, ge=10,description="评分")
    reason: str = Field(...,description="简短的推荐理由")
    address: str = Field(description="餐厅地址,没有具体餐厅则填空字符串",default="")
```

**详细规划返回报文**
```
class TravelDay(BaseModel):
    """单日行程模型"""
    day: str = Field(
        ...,
        description="行程天数标识，例如：Day 1",
        examples=["Day 1", "Day 2"]
    )
    theme: str = Field(
        ...,
        description="当日行程主题，例如：秦淮经典日",
        examples=["秦淮经典日", "金陵风味日"]
    )
    route: List[str] = Field(
        ...,
        description="按顺序排列的当日行程路线列表"
    )
    description: str = Field(
        ...,
        description="当日行程的详细游玩、美食、节奏说明"
    )


class TravelPlan(BaseModel):
    travel_plan: List[TravelDay] = Field(
        ...,
        description="完整的旅行计划列表"
    )
    saying: str = Feild(default="",description="Agent额外对用户说的话")
```

**修改返回报文**
```
{
"main_content": 主要内容，可以为“搜索返回报文”或“细规划返回报文”的格式
"saying": Agent额外对用户说的话，可以用自然语言或markdown字符串
}
```