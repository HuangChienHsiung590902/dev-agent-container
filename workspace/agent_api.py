#!/usr/bin/env python3
"""
LangGraph Agent API Server - 完整版

使用 FastAPI + LangGraph 建立 REST API
- 自動判斷是否需要使用工具
- 可循環執行直到得到最終答案
"""

import os
import sys

# 確保 Python 路徑正確
sys.path.insert(0, '/usr/local/lib/python3.10/dist-packages')

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 載入環境變數
load_dotenv("/home/agent/workspace/.env")

# ============================================================================
# LangGraph Agent Setup
# ============================================================================
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# 初始化 LLM - 使用 Ollama Qwen3.5:27b
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen3.5:27b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://10.145.119.234:11434"),
    temperature=0.7,
)

# 定義 Tools
@tool
def get_weather(location: str) -> str:
    """取得指定位置的天氣資訊"""
    weather_data = {
        "台北": "台北目前天氣晴朗，氣溫 28°C，濕度 65%",
        "台中": "台中目前天氣多雲，氣溫 26°C，濕度 70%",
        "高雄": "高雄目前天氣晴朗，氣溫 30°C，濕度 75%",
        "新加坡": "新加坡目前天氣晴朗，氣溫 32°C，濕度 80%",
        "東京": "東京目前天氣晴朗，氣溫 22°C，濕度 60%",
        "紐約": "紐約目前天氣晴朗，氣溫 18°C，濕度 50%",
    }
    return weather_data.get(location, f"{location} 的天氣資料暫時無法取得")

@tool
def calculate(expression: str) -> str:
    """簡單的計算機 - 支援基本數學運算"""
    try:
        result = eval(expression)
        return f"結果: {result}"
    except Exception as e:
        return f"計算錯誤: {str(e)}"

@tool  
def get_current_time(city: str) -> str:
    """取得指定城市的現在時間"""
    from datetime import datetime
    import pytz
    
    timezone_map = {
        "台北": "Asia/Taipei",
        "台灣": "Asia/Taipei",
        "東京": "Asia/Tokyo",
        "新加坡": "Asia/Singapore",
        "倫敦": "Europe/London",
        "紐約": "America/New_York",
        "香港": "Asia/Hong_Kong",
    }
    
    tz = timezone_map.get(city)
    if tz:
        now = datetime.now(pytz.timezone(tz))
        return f"{city} 現在時間: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    return f"無法取得 {city} 的時間"

tools = [get_weather, calculate, get_current_time]

# ============================================================================
# Slash Commands System
# ============================================================================
import re
from typing import Optional, Tuple

def parse_slash_command(message: str) -> Tuple[Optional[str], Optional[str]]:
    """解析 /command 格式的消息
    
    返回: (command, argument)
    例如: "/weather 台北" -> ("weather", "台北")
    """
    message = message.strip()
    if not message.startswith('/'):
        return None, None
    
    # 移除開頭的 /
    parts = message[1:].split(None, 1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""
    
    return command, argument.strip()

def execute_slash_command(command: str, argument: Optional[str]) -> str:
    """執行 slash command"""
    
    # /help - 顯示所有可用指令
    if command in ['help', 'h', '?']:
        return """📖 **可用指令列表:**

**/help** - 顯示所有指令
**/weather <地點>** - 查詢天氣 (例如: /weather 台北)
**/calc <算式>** - 計算數學 (例如: /calc 123*456)
**/time <城市>** - 查詢時間 (例如: /time 東京)
**/status** - 顯示系統狀態
**/skills** - 顯示所有可用技能
**/skill <名稱> [參數]** - 執行技能
**/mcp [操作]** - MCP 伺服器管理
**/model** - 顯示目前使用的模型

---
直接輸入訊息也會自動判斷是否需要使用工具！"""
    
    # /weather - 天氣查詢
    if command in ['weather', 'w']:
        if not argument:
            return "❌ 請輸入地點，例如: /weather 台北"
        result = get_weather.invoke(argument)
        return str(result)
    
    # /calc - 計算機
    if command in ['calc', 'c', '計算']:
        if not argument:
            return "❌ 請輸入算式，例如: /calc 123*456"
        result = calculate.invoke(argument)
        return str(result)
    
    # /time - 時間查詢
    if command in ['time', 't', '時間']:
        if not argument:
            return "❌ 請輸入城市，例如: /time 台北"
        result = get_current_time.invoke(argument)
        return str(result)
    
    # /status - 系統狀態
    if command in ['status', 's', '狀態']:
        return f"""🔧 **系統狀態:**

**模型:** {os.getenv('OLLAMA_MODEL', 'qwen3.5:27b')}
**Ollama:** {os.getenv('OLLAMA_BASE_URL', 'http://10.145.119.234:11434')}
**可用工具:** 天氣、計算機、時間
**版本:** 1.1.0 (Slash Commands)"""
    
    # /skills - 顯示技能列表
    if command in ['skills', 'skill', '技能']:
        return """⚡ **可用技能:**

1. **天氣查詢** - 查詢各地天氣資訊
2. **計算機** - 數學運算
3. **時間查詢** - 查詢全球城市時間
4. **AI 對話** - 使用 LLM 進行自然語言對話

輸入 /help 查看所有指令！"""
    
    # /model - 顯示模型資訊
    if command in ['model', 'm', '模型']:
        model = os.getenv('OLLAMA_MODEL', 'qwen3.5:27b')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://10.145.119.234:11434')
        return f"""🤖 **模型資訊:**

**目前使用:** {model}
**API 端點:** {base_url}
**知識截止:** 2026 年"""
    
    return f"❌ 未知指令: /{command}\n輸入 /help 查看所有可用指令"

# ============================================================================
# Skills System (類似 OpenCode 的 skill 功能)
# ============================================================================
from typing import Dict, Any, Callable
from dataclasses import dataclass
import json

@dataclass
class Skill:
    """技能定義"""
    name: str
    description: str
    aliases: list
    handler: Callable
    parameters: list = None

class SkillRegistry:
    """技能註冊表"""
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
    
    def register(self, name: str, description: str, aliases: list = None, handler: Callable = None, parameters: list = None):
        """註冊一個技能"""
        if aliases is None:
            aliases = []
        if handler is None:
            # 預設 handler
            def default_handler(args):
                return f"執行技能: {name} (參數: {args})"
            handler = default_handler
        if parameters is None:
            parameters = []
        
        skill = Skill(name=name, description=description, aliases=aliases, handler=handler, parameters=parameters)
        
        # 注册主要名称和别名
        self.skills[name.lower()] = skill
        for alias in aliases:
            self.skills[alias.lower()] = skill
    
    def get(self, name: str) -> Optional[Skill]:
        """取得技能"""
        return self.skills.get(name.lower())
    
    def list_all(self) -> list:
        """列出所有技能"""
        seen = set()
        result = []
        for skill in self.skills.values():
            if skill.name not in seen:
                seen.add(skill.name)
                result.append(skill)
        return result
    
    def execute(self, name: str, args: str) -> str:
        """執行技能"""
        skill = self.get(name)
        if not skill:
            return f"❌ 找不到技能: {name}"
        
        try:
            # 呼叫 skill 的 handler
            result = skill.handler(args)
            return result
        except Exception as e:
            return f"❌ 執行錯誤: {str(e)}"

# 創建技能註冊表
skill_registry = SkillRegistry()

# 預設技能: 搜尋網路 (使用 DuckDuckGo)
@tool
def search_web(query: str) -> str:
    """搜尋網路資訊 (使用 DuckDuckGo)"""
    if not query:
        return "❌ 請輸入搜尋關鍵字"
    
    try:
        from duckduckgo_search import DDGS
        
        ddgs = DDGS()
        results = ddgs.text(query, max_results=5)
        
        if not results:
            return f"❌ 找不到 '{query}' 的搜尋結果"
        
        output = f"🔍 搜尋結果 for '{query}':\n\n"
        
        for i, r in enumerate(results, 1):
            title = r.get('title', '無標題')
            href = r.get('href', '')
            body = r.get('body', '無內容')
            
            # 格式化輸出，不要 JSON 格式
            output += f"【{i}】{title}\n"
            output += f"   連結: {href}\n"
            output += f"   內容: {body}\n"
            output += "\n"
        
        return output.strip()
        
    except Exception as e:
        return f"❌ 搜尋錯誤: {str(e)}"

# 預設技能: 讀取網頁全文
@tool  
def fetch_url(url: str) -> str:
    """讀取網頁內容"""
    if not url:
        return "❌ 請輸入網址"
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除 script 和 style
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # 取得標題
        title = soup.title.string if soup.title else '無標題'
        
        # 取得內文
        text = soup.get_text(separator='\n')
        
        # 清理空白行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines[:500])  # 限制長度
        
        return f"📄 {title}\n\n{content}"
        
    except Exception as e:
        return f"❌ 讀取失敗: {str(e)}"

# 預設技能: 讀取檔案
@tool  
def read_file(path: str) -> str:
    """讀取檔案內容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # 限制讀取長度
            return f"📄 檔案內容 ({path}):\n\n{content}"
    except FileNotFoundError:
        return f"❌ 找不到檔案: {path}"
    except Exception as e:
        return f"❌ 讀取錯誤: {str(e)}"

# 預設技能: 寫入檔案
@tool
def write_file(path: str, content: str) -> str:
    """寫入檔案"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 已寫入檔案: {path}"
    except Exception as e:
        return f"❌ 寫入錯誤: {str(e)}"

# 預設技能: 執行命令
@tool
def run_command(cmd: str) -> str:
    """執行系統命令"""
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout or result.stderr
        return f"📟 命令輸出:\n\n{output[:500]}"
    except Exception as e:
        return f"❌ 執行錯誤: {str(e)}"

# 預設技能: 天氣預報 (進階版)
@tool
def get_forecast(location: str, days: int = 3) -> str:
    """取得天氣預報"""
    forecast_data = {
        "台北": ["今天: ☀️ 28°C", "明天: 🌤️ 27°C", "後天: 🌧️ 25°C"],
        "台中": ["今天: 🌤️ 26°C", "明天: ☀️ 28°C", "後天: 🌤️ 27°C"],
        "高雄": ["今天: ☀️ 30°C", "明天: ☀️ 31°C", "後天: 🌧️ 29°C"],
    }
    data = forecast_data.get(location, [f"{location} 天氣資料暫時無法取得"])
    result = f"📅 {location} 天氣預報 (未來 {days} 天):\n\n"
    for i, day in enumerate(data[:days], 1):
        result += f"第{i}天: {day}\n"
    return result

# 預設技能: 翻譯
@tool
def translate(text: str, target_lang: str = "英文") -> str:
    """翻譯文字"""
    return f"🌐 翻譯成 {target_lang}:\n\n「{text}」\n\n(需要連接翻譯 MCP 才能使用)"

# 註冊技能
skill_registry.register(
    name="search",
    description="搜尋網路資訊",
    aliases=["搜尋", "search", "s"],
    handler=lambda args: search_web.invoke(args) if args else "❌ 請輸入搜尋關鍵字"
)

skill_registry.register(
    name="read",
    description="讀取檔案",
    aliases=["讀取", "read", "r"],
    handler=lambda args: read_file.invoke(args) if args else "❌ 請輸入檔案路徑"
)

skill_registry.register(
    name="write",
    description="寫入檔案",
    aliases=["寫入", "write", "w"],
    handler=lambda args: "請提供檔案路徑和內容，格式: /skill write <路徑> <內容>"
)

skill_registry.register(
    name="forecast",
    description="天氣預報",
    aliases=["預報", "forecast", "f"],
    handler=lambda args: get_forecast.invoke(args) if args else "❌ 請輸入地點"
)

skill_registry.register(
    name="translate",
    description="翻譯文字",
    aliases=["翻譯", "translate", "t"],
    handler=lambda args: translate.invoke(args) if args else "❌ 請輸入要翻譯的文字"
)

skill_registry.register(
    name="run",
    description="執行系統命令",
    aliases=["執行", "run", "cmd"],
    handler=lambda args: run_command.invoke(args) if args else "❌ 請輸入命令"
)

skill_registry.register(
    name="fetch",
    description="讀取網頁全文",
    aliases=["讀取網頁", "fetch", "f2"],
    handler=lambda args: fetch_url.invoke(args) if args else "❌ 請輸入網址"
)

# 執行技能的 slash command
def execute_skill_command(command: str, argument: str) -> str:
    """執行 skill command"""
    
    # /skill - 技能管理
    if command in ['skill', 'skills', '技能']:
        if not argument:
            # 顯示所有技能
            skills = skill_registry.list_all()
            result = "⚡ **可用技能列表:**\n\n"
            for i, skill in enumerate(skills, 1):
                result += f"{i}. **{skill.name}** - {skill.description}\n"
                if skill.aliases:
                    result += f"   別名: {', '.join(skill.aliases)}\n"
            result += "\n使用方式: /skill <技能名稱> <參數>"
            return result
        
        # 執行特定技能
        parts = argument.split(None, 1)
        skill_name = parts[0]
        skill_args = parts[1] if len(parts) > 1 else ""
        
        return skill_registry.execute(skill_name, skill_args)
    
    # /mcp - MCP 管理
    if command in ['mcp', 'server', 'servers']:
        if not argument:
            return mcp_manager.status()
        
        # MCP 子命令
        mcp_parts = argument.split(None, 1)
        mcp_action = mcp_parts[0]
        mcp_args = mcp_parts[1] if len(mcp_parts) > 1 else ""
        
        return mcp_manager.execute(mcp_action, mcp_args)
    
    return None

# ============================================================================
# MCP (Model Context Protocol) Support
# ============================================================================
import asyncio
import subprocess
from typing import List, Dict, Any

class MCPManager:
    """MCP 伺服器管理器"""
    
    def __init__(self):
        self.servers: Dict[str, dict] = {}
        self.tools: List[dict] = []
    
    def add_server(self, name: str, command: str, args: list = None):
        """新增 MCP 伺服器"""
        if args is None:
            args = []
        
        self.servers[name] = {
            "command": command,
            "args": args,
            "status": "stopped",
            "process": None
        }
        return f"✅ 已新增 MCP 伺服器: {name}"
    
    def remove_server(self, name: str):
        """移除 MCP 伺服器"""
        if name in self.servers:
            del self.servers[name]
            return f"✅ 已移除 MCP 伺服器: {name}"
        return f"❌ 找不到 MCP 伺服器: {name}"
    
    def list_servers(self) -> str:
        """列出所有 MCP 伺服器"""
        if not self.servers:
            return "📡 **MCP 伺服器:**\n\n目前沒有連接的伺服器\n\n使用 /mcp add <名稱> <命令> 來新增"
        
        result = "📡 **MCP 伺服器列表:**\n\n"
        for name, server in self.servers.items():
            status = server.get("status", "unknown")
            result += f"- **{name}** ({status})\n"
            result += f"  命令: {server['command']} {' '.join(server.get('args', []))}\n"
        return result
    
    def status(self) -> str:
        """MCP 狀態"""
        return self.list_servers() + f"\n\n⚠️ 注意: 目前 MCP 功能需要完整的 MCP 伺服器環境"
    
    def execute(self, action: str, args: str) -> str:
        """執行 MCP 操作"""
        
        if action in ['add', '新增']:
            # /mcp add <name> <command>
            parts = args.split(None, 1)
            if len(parts) < 2:
                return "❌ 請提供伺服器名稱和命令\n格式: /mcp add <名稱> <命令>"
            name = parts[0]
            command = parts[1]
            return self.add_server(name, command)
        
        if action in ['remove', 'rm', '刪除']:
            return self.remove_server(args)
        
        if action in ['list', 'ls', '列表']:
            return self.list_servers()
        
        return f"❌ 未知操作: {action}\n可用操作: add, remove, list"

# 創建 MCP 管理器
mcp_manager = MCPManager()

# 預設新增一些常見的 MCP 伺服器配置（只是配置，還沒連接）
# mcp_manager.add_server("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/path"])

# ============================================================================
# LangGraph - 完整版 (使用 prebuilt create_react_agent)
# ============================================================================
from langgraph.prebuilt import create_react_agent

graph = create_react_agent(llm, tools)

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(title="LangGraph Agent API (完整版)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/")
def root():
    return {
        "name": "LangGraph Agent API (完整版)",
        "version": "1.0.0",
        "status": "running",
        "description": "自動判斷並呼叫工具的 Agent"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """聊天端點 - 使用 LangGraph 完整版 Agent"""
    try:
        # 檢查是否為 slash command
        command, argument = parse_slash_command(request.message)
        if command:
            # 檢查是否為 skill 或 mcp command
            skill_result = execute_skill_command(command, argument or "")
            if skill_result:
                return ChatResponse(response=skill_result)
            
            # 執行一般的 slash command
            response_text = execute_slash_command(command, argument)
            return ChatResponse(response=response_text)
        
        from langchain_core.messages import HumanMessage, AIMessage
        
        # 透過 LangGraph 執行
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"recursion_limit": 10}  # 最多迴圈 10 次
        )
        
        print("Result keys:", result.keys())
        print("Messages count:", len(result.get("messages", [])))
        
        # 取得最後的回覆
        last_message = result["messages"][-1]
        
        print("Last message type:", type(last_message))
        print("Last message content:", last_message.content[:100] if hasattr(last_message, 'content') else "N/A")
        
        # 處理回覆內容
        content = last_message.content
        if isinstance(content, list):
            response_text = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    response_text = block.get("text", "")
                    break
        else:
            response_text = str(content)
        
        return ChatResponse(response=response_text)
    except Exception as e:
        import traceback
        error_detail = str(e) + "\n" + traceback.format_exc()
        print("Error:", error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

# ============================================================================
# Main
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("LangGraph Agent API (完整版)")
    print("=" * 60)
    print("可用工具: 天氣查詢、計算機、時間查詢")
    print("API 文件: http://localhost:8000/docs")
    print("")
    print("範例:")
    print('  curl -X POST http://localhost:8000/chat \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"message": "台北天氣怎麼樣？"}')
    print("")
    print('  curl -X POST http://localhost:8000/chat \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"message": "123 * 456 = ?"}')
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
