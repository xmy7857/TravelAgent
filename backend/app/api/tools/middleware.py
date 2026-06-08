import os
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable
from langchain.tools import tool, ToolRuntime
from ..schemas.schemas import SupportState,Context,configs
from langchain.messages import SystemMessage
from typing import Callable, TypedDict 
# 2. 工具通过 Command 更新 current_step

SKILLS={"chat":[],"search":[],"plan":[],"weather":[],"travel":[]}
@tool
def transfer_status(
    next_step: str,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """转移到下一步，步骤共有以下三种。
    聊天问答：next_step=chat；
    搜索景点与美食或修改感兴趣的景点美食：next_step=search；
    出行安排规划或修改：next_step=plan；
    """
    intent_dict = {"chat":"聊天问答","search":"搜索景点与美食","plan":"出行安排规划，请通过load_skill工具调用plan技能以获取具体规划流程"}
    print(f"当前用户需要{intent_dict[next_step]}")
    return Command(update={
        "messages": [
            ToolMessage(
                content=f"当前用户需要{intent_dict[next_step]}",
                tool_call_id=runtime.tool_call_id
            )
        ],
        # 转移到下一步
        "current_step": next_step
    })

# # 将步骤映射到其配置



class Skill(TypedDict):
    """
    技能结构体：用于向智能体逐步披露的技能格式
    严格按照你要求的字段定义
    """
    name: str              # 技能唯一标识（英文ID）
    description: str       # 1-2句话简介（用于系统提示词）
    content: str           # 技能详细内容（调用load_skill工具后返回的内容）



def load_skills_from_skill_dir(skill_dir: str = ".skills") -> list[Skill]:
    """
    从 .skill/SKILL.md 中读取技能
    格式规则：
    1. 头部是 key: value 元数据（name, description）
    2. 用 --- 分隔头部与正文
    3. --- 下方所有内容直接作为 content，不解析 markdown
    """
    skill_dir = os.path.join(os.getcwd(), "backend", skill_dir)
    global SKILLS
    for agent in os.listdir(skill_dir):
        agent_skill_dir = os.path.join(skill_dir, agent)
        for agent_skill in os.listdir(agent_skill_dir):
            skill_file=os.path.join(agent_skill_dir,agent_skill,"SKILL.md")
            if not os.path.exists(skill_file):
                continue

            # 读取全部内容
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 按 --- 分割元数据部分 和 正文部分
            if "---" not in content:
                continue

            header_part, _, content_part = content.partition("---")

            # 初始化字段
            name = ""
            description = ""

            # 逐行解析头部元数据
            for line in header_part.splitlines():
                line = line.strip()
                if not line:
                    continue

                # 提取 name
                if line.startswith("name:"):
                    name = line[len("name:"):].strip()

                # 提取 description（支持带引号、不带引号）
                elif line.startswith("description:"):
                    desc = line[len("description:"):].strip()
                    # 去掉首尾引号（如果有）
                    if (desc.startswith('"') and desc.endswith('"')) or (desc.startswith("'") and desc.endswith("'")):
                        desc = desc[1:-1]
                    description = desc

            # 构造最终 Skill（严格按你要求的格式）
            skill = Skill(
                name=name,
                description=description,
                content=content_part.strip()
            )
            SKILLS[agent].append(skill)

    return


@tool
def load_skill(skill_name: str, runtime: ToolRuntime[None, Context]) -> str:#用于加载技能runtime是运行状态，不用跟模型说，系统会自动传入。
    """Load the full content of a skill into the agent's context.
    
    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "expense_reporting", "travel_booking")
    """
    # Find and return the requested skill
    for skill in SKILLS[runtime.context.current_step]:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS[runtime.context.current_step])
    return f"Skill '{skill_name}' not found. Available skills: {available}"


'''中间件有两种配置方式.
1是用装饰器
@wrap_model_call
async def apply_step_config():
2是用类
class ApplyStepConfig(AgentMiddleware):
async def awrap_model_call():
注意，装饰器中没有a，类方法中有a
'''

class ApplyStepConfig(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt."""

    # Register the load_skill tool as a class variable
    tools = [load_skill,transfer_status]

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        print("初始化中间件")
        load_skills_from_skill_dir()

    async def awrap_model_call(
        self,
        request: ModelRequest,#这个是最全的模型状态，包括message，toolruntime之类的
        handler: Callable[[ModelRequest], ModelResponse]#最终要调用的模型
    ) -> ModelResponse:
        """根据 current_step 配置智能体行为。"""
        step = request.state.get("current_step", "chat")#看看当前状态是什么
        print(f"已切换至{step}")
        
        skills_list = []
        for skill in SKILLS[step]:#搜索该状态可能会用到的skill
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        if len(skills_list) > 0:
            skills_list_str = "\n".join(skills_list)
            skills_prompt = f"\n\n## 可用的 Skills（调用load_skill工具来使用他们）\n\n{skills_list_str}\n\n当您需要有关处理特定类型请求的详细信息时，请使用 load_skill 工具。"
        else:
            skills_prompt = ""#如果有可用的skill，就把他的名字和描述放到系统提示词里面，提醒模型可以用他
        
        config = configs[step]#调取当前状态的配置，包括系统提示词和工具列表
        request.runtime.context.current_step = step  # 确保 current_step 在 context 中可用
        request = request.override(
            system_prompt=config["prompt"]+skills_prompt,#配置该状态的提示词
            tools=config["tools"]+self.tools#配置该状态的工具
        )
        return await handler(request)#运行模型