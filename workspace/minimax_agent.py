#!/usr/bin/env python3
"""
LangChain Agent 使用 Minimax (Anthropic API 兼容)

支援的模型:
- MiniMax-M2.5 (推薦)
- MiniMax-M2.5-highspeed
- MiniMax-M2.1
- MiniMax-M2.1-highspeed
- MiniMax-M2
"""

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# ============================================================================
# 方式 1: 直接使用 Anthropic SDK
# ============================================================================
def basic_example():
    """基本 API 調用"""
    import anthropic
    
    client = anthropic.Anthropic(
        api_key=os.getenv("MINIMAX_API_KEY")
    )
    
    message = client.messages.create(
        model="MiniMax-M2.5",
        max_tokens=1000,
        system="你是一個專業的 AI 助手，請用繁體中文回答問題。",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "你好！請自我介紹一下。"
                    }
                ]
            }
        ]
    )
    
    for block in message.content:
        if block.type == "thinking":
            print(f"思考過程: {block.thinking}\n")
        elif block.type == "text":
            print(f"回覆: {block.text}")


# ============================================================================
# 方式 2: 使用 LangChain + Anthropic (推薦 for Agent)
# ============================================================================
def langchain_anthropic_example():
    """使用 LangChain 的 Anthropic 集成"""
    from langchain_anthropic import ChatAnthropic
    
    llm = ChatAnthropic(
        model="MiniMax-M2.5",
        anthropic_api_key=os.getenv("MINIMAX_API_KEY"),
        temperature=1.0,
        max_tokens=2048,
    )
    
    from langchain.schema import HumanMessage, SystemMessage
    
    messages = [
        SystemMessage(content="你是一個專業的 AI 助手，請用繁體中文回答。"),
        HumanMessage(content="什麼是 LangChain？")
    ]
    
    response = llm.invoke(messages)
    print(f"回覆: {response.content}")


# ============================================================================
# 方式 3: LangChain Agent (有 Tools)
# ============================================================================
def agent_example():
    """使用 LangChain Agent + Tools"""
    from langchain_anthropic import ChatAnthropic
    from langchain.agents import AgentType, create_tool_calling_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import Tool
    
    # 初始化 LLM
    llm = ChatAnthropic(
        model="MiniMax-M2.5",
        anthropic_api_key=os.getenv("MINIMAX_API_KEY"),
        temperature=1.0,
    )
    
    # 定義 Tools
    def get_weather(location: str) -> str:
        """取得指定位置的天氣資訊"""
        weather_data = {
            "台北": "台北目前天氣晴朗，氣溫 28°C，濕度 65%",
            "台中": "台中目前天氣多雲，氣溫 26°C，濕度 70%",
            "高雄": "高雄目前天氣晴朗，氣溫 30°C，濕度 75%",
        }
        return weather_data.get(location, f"{location} 的天氣資料暫時無法取得")
    
    def calculate(expression: str) -> str:
        """簡單的計算機"""
        try:
            # 注意：實際使用時應該使用安全的 eval 或 parse
            result = eval(expression)
            return f"結果: {result}"
        except Exception as e:
            return f"計算錯誤: {str(e)}"
    
    tools = [
        Tool(
            name="天氣查詢",
            func=get_weather,
            description="當用戶詢問天氣時使用此工具。輸入是位置名稱，如「台北」、「台中」。"
        ),
        Tool(
            name="計算機",
            func=calculate,
            description="當用戶需要數學計算時使用此工具。輸入是數學表達式，如「2+2」、「10*5」。"
        )
    ]
    
    # 建立 Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一個專業的 AI 助手。
當用戶詢問天氣時，必須使用「天氣查詢」工具。
當用戶需要計算時，必須使用「計算機」工具。
請用繁體中文回答。"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 執行
    query = "台北的天氣怎麼樣？還有 123 * 456 是多少？"
    print(f"\n用戶輸入: {query}\n")
    
    result = agent.invoke({"input": query})
    print(f"Agent 回覆: {result['output']}")


# ============================================================================
# 方式 4: LangGraph (新一代 Agent 框架)
# ============================================================================
def langgraph_example():
    """使用 LangGraph 建立 Agent"""
    from langgraph.prebuilt import create_react_agent
    from langchain_anthropic import ChatAnthropic
    
    llm = ChatAnthropic(
        model="MiniMax-M2.5",
        anthropic_api_key=os.getenv("MINIMAX_API_KEY"),
    )
    
    # 簡單的 tools
    def get_time(location: str) -> str:
        """取得指定位置的現在時間"""
        import datetime
        return f"{location} 的現在時間是 {datetime.datetime.now().strftime('%H:%M:%S')}"
    
    tools = [get_time]
    
    # 建立 Agent
    agent = create_react_agent(llm, tools)
    
    # 執行
    query = "台北現在幾點？"
    print(f"\n用戶輸入: {query}\n")
    
    result = agent.invoke({"messages": [("human", query)]})
    print(f"Agent 回覆: {result['messages'][-1].content}")


# ============================================================================
# 主程式
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("LangChain + Minimax Agent 範例")
    print("=" * 60)
    
    # 檢查 API Key
    if not os.getenv("MINIMAX_API_KEY"):
        print("錯誤: 請在 .env 檔案中設定 MINIMAX_API_KEY")
        exit(1)
    
    print("\n--- 方式 1: 基本 Anthropic SDK ---")
    basic_example()
    
    print("\n--- 方式 2: LangChain + Anthropic ---")
    langchain_anthropic_example()
    
    print("\n--- 方式 3: LangChain Agent (有 Tools) ---")
    agent_example()
    
    print("\n--- 方式 4: LangGraph Agent ---")
    langgraph_example()
