from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from .schemas.schemas import SearchRequest, SearchResult, AgentResponse,Context,configs
from .memory.session import SessionManager
from langchain_openai import ChatOpenAI
from .agents import agents
from .tools import tools
from .tools.middleware import load_skill
from langchain.agents import AgentState
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
import re
# from .routes import trip, poi, map as map_routes
'''
任务：
1、如何正常运行12306-mcp
2、如何减少plan的推理时间（一个思路是不要让agent调用这么多次工具，调用了以后把结果存储在store里，后面要用就直接读取）
3、美化plan的界面，搞个动态地图？
4、搞个小红书rag
5、其他细化功能，强化亮点
6、加个机票mcp？
8、把skill搞成现场读文件的？
'''
def extract_json_code_block(text: str) -> str:
    """
    从字符串中提取 ```json ... ``` 包裹的内容，并移除所有空白字符（空格、换行、制表符等）
    
    Args:
        text: 包含 json 代码块的原始字符串
        
    Returns:
        提取并清理后的纯JSON字符串（无任何空白）
        
    Raises:
        ValueError: 未找到匹配的 json 代码块时抛出异常
    """
    # 正则表达式：匹配 ```json 开头，``` 结尾，非贪婪匹配中间内容
    # re.DOTALL 让 . 可以匹配换行符
    pattern = r"```json(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    

    if not match:
        return text
    
    # 获取中间的JSON内容
    json_clean = match.group(1).strip()
    
    return json_clean

# 获取配置
settings = get_settings()
llm = ChatOpenAI(model=settings.model_name, base_url=settings.base_url, api_key=settings.api_key)
store_manager = InMemoryStore()
session_manager = SessionManager(llm,clean_interval=6000,max_time_limit=30000)
client = None
train_tools = []
amap_tools = []
weather_tools = []

@asynccontextmanager#在启动时执行这个
async def get_mcp_tools(app: FastAPI):
    global client,train_tools,amap_tools,weather_tools#这几个工具要是全局变量，这样外面的函数才能拿得到
    global  weather_agent,travel_agent,route_agent
    client = MultiServerMCPClient(
        {
            "12306-mcp":{
                "transport": "stdio",
                "command": "/usr/local/nvm/versions/node/v24.15.0/bin/npx",
                "cwd": "/opt/data/private/llm/",
                "args": ["-y","12306-mcp"],
                "env": {"NODE_OPTIONS": "--dns-result-order=ipv4first"}
            },
            "amap":{
                "transport": "stdio",
                "command": "/opt/data/private/miniconda3/envs/clbot/bin/uvx",
                "args": ["amap-mcp-server"],
                "env": {"AMAP_MAPS_API_KEY": settings.amap_api_key}
            }
        }
    )
    async with client.session("12306-mcp") as session_12306:
        async with client.session("amap") as session_amap:
            train_tools = await load_mcp_tools(session_12306)
            print(f"找到{len(train_tools)}个工具")
            amap_tools = await load_mcp_tools(session_amap)
            print(f"找到{len(amap_tools)}个工具")
            weather_tools = [tool for tool in amap_tools if tool.name == "maps_weather"]
            # configs["chat"]["tools"]#+=[tools.transfer_status]
            # configs["chat"]["tools"]+=amap_tools#,tools.get_spotfood,tools.write_spotfood
            configs["search"]["tools"]+=[tools.get_weather]
            configs["plan"]["tools"]+=amap_tools#,tools.get_plan,tools.write_plan,tools.get_spotfood,
            configs["plan"]["tools"]+=[tools.get_weather]
            print("plan agent工具数：",len(configs["plan"]["tools"]))
            weather_agent = agents.WeatherAgent(llm,tools=weather_tools+[load_skill])#创建天气智能体
            travel_agent = agents.TravelPlanAgent(llm,tools=train_tools)#创建车票查询智能体
            route_agent = agents.RouteAgent(llm,tools = amap_tools+[tools.get_weather,load_skill],store_manager=store_manager)#创建主智能体，通过中间件可实现chat、search、plan三个状态的切换。这里要把每个子状态可能用到的工具全部传入，要不然会报错
            yield#把状态固定在这里，长连接不会退出
            


# 创建FastAPI应用
app = FastAPI(#固定写法
    title=settings.app_name,
    version=settings.app_version,
    description="智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=get_mcp_tools
)

# 配置CORS
app.add_middleware(#固定写法
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")#有了@asynccontextmanager之后，这个函数不会被执行
async def startup_event():
    """应用启动事件"""
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)
    
    # 打印配置信息
    print_config()
    
    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise
    
    print("\n" + "="*60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("="*60 + "\n")



@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("\n" + "="*60)
    print("👋 应用正在关闭...")
    print("="*60 + "\n")

@app.post('/chat')#这里是请求的入口。注意：暴露给客户端的地址要用aimax平台给的端口，要不然会被防火墙栏。这里不用
async def myagent(request:SearchRequest) -> AgentResponse:
    print("用户请求：",request)
    session_manager.update_history(request.session_id,request.model_dump_json(),role="user")#历史记录管理器，更新历史记录
    request_state = store_manager.get((request.user_id,request.session_id),"request_state")#看看之前有没有存储过天气信息
    request_state_change = (request_state is None) or request_state.value["city"] != request.city or request_state.value["date_departure"] != request.date_departure or request_state.value["days"] != request.days
    if request_state_change:#如果有存储过并且天气信息没有改变，就不再次存储了
        ##查询天气和车票
        reply_travel = await travel_agent.chat(request)#运行车票agent查询车票信息
        reply_weather = await weather_agent.chat(request)#运行天气agent查询天气信息
        request_state_dict = {"city":request.city,"date_departure":request.date_departure,"days":request.days,"weather":reply_weather,"travel":reply_travel}
        store_manager.put((request.user_id,request.session_id),"request_state",request_state_dict)#更新状态
    else:
        reply_travel=request_state.value["travel"]
        reply_weather=request_state.value["weather"]
    history = session_manager.query(request.session_id)#查询历史记录
    reply = await route_agent.chat(request.user_id,request.session_id,history)#启动主agent
    session_manager.update_history(request.session_id,reply,role="ai")#把ai输出存入历史记录

    return AgentResponse(user_id=request.user_id, 
                         session_id=request.session_id, 
                         ai_message=reply,
                         weather=reply_weather,
                         travel_mode=reply_travel)
    
