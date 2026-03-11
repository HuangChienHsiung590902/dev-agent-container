# Dev Agent Container

專為 AI 開發 Agent 設計的 Docker 開發環境。

## 功能特色

- **完整開發工具鏈**
  - Node.js 22.x
  - Python 3 + pip + pipenv/poetry
  - Go 1.21
  - Rust (stable)
  
- **Docker-in-Docker (DinD)**
  - 內建 Docker daemon
  - 可在容器內建置和執行 Docker 映像檔
  - 支援 docker-compose
  
- **實用工具**
  - Git + Git LFS
  - build-essential, cmake
  - vim, nano, htop, tree, jq
  - curl, wget, rsync
  
- **開發體驗**
  - 非 root 使用者 (agent)
  - 已安裝常用 Python 開發工具 (black, pytest, mypy)
  - 預設時區: Asia/Taipei

- **LangChain AI 開發**
  - langchain, langchain-core, langchain-community
  - langchain-openai, langchain-anthropic
  - langgraph (新一代 Agent 框架)
  - chromadb, faiss-cpu (向量資料庫)
  - jupyter (互動式開發)

## 快速開始

### 前置需求

- Docker Engine 20.10+
- Docker Compose V2

### 建置與啟動

```bash
# 進入專案目錄
cd dev-agent-container

# 建置 image
docker-compose build

# 啟動容器 (互動模式)
docker-compose up -d
docker exec -it dev-agent bash

# 停止容器
docker-compose down
```

### 使用 DinD

容器啟動後，Docker daemon 會自動執行：

```bash
# 在容器內驗證 Docker
docker ps
docker run hello-world

# 建置映像檔
docker build -t my-app .

# 使用 docker-compose
docker-compose up -d
```

## 目錄結構

```
dev-agent-container/
├── Dockerfile           # Image 定義
├── docker-compose.yml   # 容器编排配置
├── .dockerignore       # 忽略清單
├── README.md           # 本文件
└── workspace/          # 開發工作目錄 (自動建立)
```

## 資源配置

可在 `docker-compose.yml` 中調整：

```yaml
services:
  dev-agent:
    mem_limit: 4g      # 記憶體限制
    cpus: 2           # CPU 核心數
```

## 開發建議

### 進入容器開發

```bash
# 啟動並進入 shell
docker-compose up -d
docker exec -it dev-agent bash

# 如果有 workspace 目錄
docker exec -it dev-agent bash -c "cd /home/agent/workspace && bash"
```

### 存取主機 Docker (替代方案)

若不需 DinD，可改用 host Docker socket：

1. 註釋掉 `privileged: true`
2. 取消註釋 volume mount:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

## 驗證安裝

```bash
# 登入後自動顯示版本資訊
node --version     # v22.x.x
npm --version      # 10.x.x
python3 --version  # 3.10.x
pip --version
go version         # go1.21.6
rustc --version    # 1.75.x
docker --version   # Docker version 24.x
```

## LangChain 開發

### 快速開始

```bash
# 進入容器
docker exec -it dev-agent bash

# 建立專案
cd /home/agent/workspace
mkdir my-agent && cd my-agent

# 建立簡單的 Agent
cat > agent.py << 'EOF'
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# 簡單的天氣查詢 tool (模擬)
def get_weather(location: str) -> str:
    """取得指定位置的天氣資訊"""
    return f"{location} 目前天氣晴朗，溫度 25°C"

tools = [
    Tool(
        name="天氣查詢",
        func=get_weather,
        description="當用戶詢問天氣時使用此工具"
    )
]

# 建立 Agent
llm = ChatOpenAI(model="gpt-4", api_key="your-api-key")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一個有用的助手。"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
])

agent = create_openai_functions_agent(llm, tools, prompt)

# 執行
result = agent.invoke({"input": "台北的天氣怎麼樣？"})
print(result["output"])
EOF

# 執行
python3 agent.py
```

### 使用 Jupyter Notebook

```bash
# 啟動 Jupyter
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
```

### 常見 LangChain 組合

| 用途 | 套件 |
|------|------|
| OpenAI | `langchain-openai` |
| Anthropic (Claude) | `langchain-anthropic` |
| 本地模型 (Ollama) | `langchain-ollama` |
| 向量儲存 | `chromadb`, `faiss-cpu`, `pinecone` |
| Agent 框架 | `langgraph` |
| RAG | `langchain-community`, `langchain-text-splitters` |

## Minimax API 整合

### 支援的模型

| 模型名稱 | Context Window | 說明 |
|----------|----------------|------|
| MiniMax-M2.5 | 204,800 | 最高效能 (約 60 tps) |
| MiniMax-M2.5-highspeed | 204,800 | 高速版本 (約 100 tps) |
| MiniMax-M2.1 | 204,800 | 強大多語言程式能力 |
| MiniMax-M2.1-highspeed | 204,800 | 高速版本 |
| MiniMax-M2 | 204,800 | Agent 能力、進階推理 |

### 使用方式

1. 複製環境變數範例:
```bash
cd /home/agent/workspace
cp .env.example .env
# 編輯 .env 填入你的 API Key
```

2. 執行範例:
```bash
python3 minimax_agent.py
```

3. 或直接在 Python 中使用:

```python
import os
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(
    model="MiniMax-M2.5",
    anthropic_api_key=os.getenv("MINIMAX_API_KEY"),
)

response = llm.invoke("你好，請用繁體中文自我介紹")
print(response.content)
```

### 環境變數

```bash
export ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic
export ANTHROPIC_API_KEY=your-api-key
```

## 故障排除

### Docker daemon 啟動失敗

```bash
# 手動啟動 Docker
dockerd &

# 或檢查日誌
docker logs dev-agent
```

### 權限問題

確保使用非 root 使用者:

```bash
# 預設以 agent 使用者登入
docker exec -it dev-agent bash
```

### 磁碟空間不足

清理 Docker 資源:

```bash
docker system prune -a
docker volume prune
```

## License

MIT
