from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date
from enum import Enum
from dataclasses import dataclass
from langchain.agents import AgentState
from ..prompt import prompt as prt

configs = {
    "chat": {
        "prompt": prt.ROUTE_AGENT,
        "tools": []
    },
    "search": {
        "prompt": prt.SEARCH_AGENT,
        "tools": []
    },
    "plan": {
        "prompt": prt.TRIP_PLAN_AGENT,
        "tools": []
    }
}

@dataclass
class Context:
    user_id: str = None
    session_id: str = None
    current_step: str = "chat"

class SupportState(AgentState):
    """跟踪当前处于哪个步骤。"""
    current_step: str = "chat"

class Intent(str, Enum):#枚举类型
    """用户意图枚举类型
    
    定义系统可以识别的用户意图类型：
    - modify_list: 用户想要修改其感兴趣的景点或美食
    - pass_list: 用户对当前确定的景点或美食感到满意，可以进一步进行行程规划
    - modify_plan：用户想要对行程规划进行修改
    - unknown: 用户没有上述意图
    """
    modify_list = 0   # 用户想要修改其感兴趣的景点或美食
    pass_list = 1     # 用户对当前确定的景点或美食感到满意，可以进一步进行行程规划
    modify_plan = 2   # 用户想要对行程规划进行修改
    unknown = 3       # 用户没有上述意图
class AgentRequest(BaseModel):
    user_id: str = Field(...,description="用户编号")
    session_id: str = Field(...,description="会话编号")
    user_message: str = Field(...,description="用户消息")

class AgentResponse(BaseModel):
    user_id: str = Field(...,description="用户编号")
    session_id: str = Field(...,description="会话编号")
    ai_message: str = Field(...,description="用户消息")
    weather: str = Field(default="",description="天气情况")
    travel_mode: str = Field(default="",description="推荐的列车车次列表")

class SearchRequest(BaseModel):
    user_id: str = Field(...,description="用户编号")
    session_id: str = Field(...,description="会话编号")
    city_departure: str = Field(...,description="出发城市")
    date_departure: str = Field(...,description="出发日期")
    city: str = Field(...,description="用户计划到达的城市")
    days: int = Field(...,description="用户计划游玩的天数")
    user_prompt: str = Field(description="用户要求",default="")

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

class SearchResult(BaseModel):
    city: str = Field(...,description="用户计划出行的城市")
    days: int = Field(...,description="用户计划游玩的天数")
    attractions: list[AttrItem] = Field(...,description="景点列表")
    foods: list[FoodItem] = Field(...,description="美食列表")

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