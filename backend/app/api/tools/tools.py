from langchain.tools import tool, ToolRuntime
from ..schemas.schemas import Context
@tool
def get_weather(runtime: ToolRuntime[Context]) -> str:
    """获取当前天气
    """
    print("正在查询天气")
    # 访问 store - 与提供给 `create_agent` 的 store 相同
    store = runtime.store # [!code highlight]
    user_id = runtime.context.user_id
    session_id = runtime.context.session_id

    # 从 store 检索数据 - 返回带有 value 和 metadata 的 StoreValue 对象
    
    user_info = store.get((user_id,session_id), 'request_state') # [!code highlight]
    if not user_info:
        return "无法查询天气"
    return str(user_info.value["weather"])

@tool
def weather(city: str, date: str):
    """根据城市和日期查询天气情况，
    Args：city填城市名，如‘南京’，date填日期，如‘2026-05-01’
    """
    return "中到大雨，南风1~2级"



@tool
def get_plan(runtime: ToolRuntime[Context]) -> str:
    """获取当前的行程规划。如果用户希望对当前以规划的出行安排进行修改或查询，可以调用这个工具
    """
    print("正在查询出行安排")
    # 访问 store - 与提供给 `create_agent` 的 store 相同
    store = runtime.store # [!code highlight]
    user_id = runtime.context.user_id
    session_id = runtime.context.session_id
    # 从 store 检索数据 - 返回带有 value 和 metadata 的 StoreValue 对象
    
    user_info = store.get((user_id,session_id), 'plan') # [!code highlight]
    if not user_info:
        return "当前还没有创建出行安排"
    return str(user_info)