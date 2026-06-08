from ..memory.memory import Memory
from datetime import datetime,timedelta
import time
import threading

class Session:
    def __init__(self,**args):
        self.memory = Memory(**args)
        self.total_tokens = 0
        self.last_activate_time = datetime.now()

class SessionManager:
    def __init__(self,llm,clean_interval=60,max_time_limit=300):
        self.sessions: dict[str,Session] = {}
        self.llm = llm
        self.clean_interval=clean_interval
        self.max_time_limit=timedelta(seconds=max_time_limit)
        self.start_clean_loop()
    def query(self,session_id: str):
        self.activate_session(session_id)#使会话活跃
        if session_id in self.sessions:
            return self.sessions[session_id].memory.load_messages()
        else:
            self.sessions[session_id]=Session(llm=self.llm)
            return self.sessions[session_id].memory.load_messages()
    def update_history(self,session_id, history_delta, role):
        assert role=="user" or role=="ai"
        if role == "user":
            if session_id not in self.sessions:
                self.sessions[session_id]=Session(llm=self.llm)
            self.sessions[session_id].memory.add_user_message(history_delta)
        else:
            if session_id not in self.sessions:
                self.sessions[session_id]=Session(llm=self.llm)
            self.sessions[session_id].memory.add_ai_message(history_delta)
    def empty(self,session_id):#清空某个会话
        assert session_id in self.sessions
        self.sessions[session_id].memory.clear_memory()
    def activate_session(self,session_id):
        assert session_id in self.sessions
        self.sessions[session_id].last_activate_time = datetime.now()
    
    def clean_loop(self):
        while True:
            #检查久不活跃的会话
            print("检查不活跃的会话")
            timeout_sessions = self.find_timeout_session()
            #清理这些会话
            print(f"清空{timeout_sessions}")
            for del_sessionid in timeout_sessions:
                del self.sessions[del_sessionid]
            time.sleep(self.clean_interval)
            #睡眠
    def find_timeout_session(self):
        timeout = []
        nowtime = datetime.now()
        for id in self.sessions.keys():
            if nowtime-self.sessions[id].last_activate_time > self.max_time_limit:
                timeout.append(id)
        return timeout
    def start_clean_loop(self):
        self._thread = threading.Thread(target=self.clean_loop,daemon=True)
        self._thread.start()
        print("线程已启动")