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
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# 初始化 LLM
llm = ChatAnthropic(
    model="MiniMax-M2.5",
    anthropic_api_key=os.getenv("MINIMAX_API_KEY"),
    temperature=1.0,
    max_tokens=4096,
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
