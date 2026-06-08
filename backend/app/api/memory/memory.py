from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationSummaryBufferMemory
class Memory:
    def __init__(self,llm:ChatOpenAI,max_token: int=2000, memory_key: str="history"):
        self.llm = llm
        self.max_token = max_token
        self.memory_key = memory_key
        self._memory = ConversationSummaryBufferMemory(llm=self.llm, max_token_limit=self.max_token, memory_key=self.memory_key)
    
    def add_user_message(self,message: str):
        self._memory.chat_memory.add_user_message(message)
    def add_ai_message(self,message: str):
        self._memory.chat_memory.add_ai_message(message)
    def clear_memory(self):
        self._memory.clear()
    def load_messages(self) -> list:
        messages = self._memory.load_memory_variables({})[self.memory_key]
        return messages