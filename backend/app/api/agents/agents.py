from langchain_openai import ChatOpenAI
from ..schemas.schemas import SearchRequest, SearchResult, AgentResponse, Context, SupportState,configs
from ..prompt import prompt as prt
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore
from ..tools.middleware import ApplyStepConfig
import json
import re



class RouteAgent:
    def __init__(self, llm: ChatOpenAI, tools, store_manager: InMemoryStore):
        self._llm = llm
        self._agent = create_agent(
            model=self._llm,
            system_prompt=prt.ROUTE_AGENT,
            tools=tools,
            store=store_manager,
            state_schema=SupportState,#这里不要加括号
            middleware=[ApplyStepConfig()]#应用了缠绕式中间件，所以每次开始时都会先经过中间件。注意这里要加括号
            ##中间件有两种，一种是结点式中间件，只在模型调用前/调用后执行一次；还有一种是缠绕式中间件，在模型每次调用时都会执行
        )
    def extract_response(self,result):
        reply = result["messages"][-1].content
        return reply
    async def chat(self, user_id: str, session_id: str, history: list) -> str:
        result = await self._agent.ainvoke({"messages":history},context=Context(user_id=user_id, session_id=session_id))#利用context保存上下文，调用这个之前，首先经过中间件
        reply = self.extract_response(result)#提取信息
        print(reply)
        
        return reply
    
    
class TravelPlanAgent:
    def __init__(self, llm: ChatOpenAI, tools, max_iter = 10):
        self._llm = llm
        self._max_iter = max_iter
        self._agent = create_agent(
                model=self._llm,
                tools=tools,
                system_prompt=prt.TRAVEL_PLAN_AGENT,
            )

    def build_prompt(self,message: SearchRequest):
        return f"我出发的城市/地区为：{message.city_departure}，计划到达的城市为{message.city}，计划{message.date_departure}出发，请帮我查询火车/高铁票，以JSON格式返回"
    async def chat(self, message: SearchRequest) -> str:
        user_prompt = self.build_prompt(message)#生成prompt
        history = {"messages":[user_prompt]}
        
        result = await self._agent.ainvoke(history,context=Context(user_id=message.user_id, session_id=message.session_id, current_step="travel"))
        reply = self.extract_response(result)
        return reply
    
    def extract_response(self,result):
        reply = result["messages"][-1].content
        return reply

class WeatherAgent:
    def __init__(self, llm: ChatOpenAI, tools):
        self._llm = llm
        self._agent = create_agent(
                model=self._llm,
                tools=tools,
                system_prompt=prt.WEATHER_AGENT
            )
    def build_prompt(self,request: SearchRequest) -> str:
        return f"我将于{request.date_departure}出发到{request.city}旅行{request.days}天，请帮我查看目的地天气情况。结果以JSON格式返回"
    async def chat(self,request: SearchRequest) -> str:
        """user_prompt是自然语言字符串"""
        user_prompt = self.build_prompt(request)
        message = {"messages":user_prompt}
        result = await self._agent.ainvoke(message, context=Context(user_id=request.user_id, session_id=request.session_id, current_step="weather"))
        reply = self.extract_response(result)
        return reply
    def extract_response(self,result):
        reply = result["messages"][-1].content
        return reply
    




