#!/usr/bin/env python3
"""
Agent TUI - 使用 Textual 建立的文字介面
"""
import os
import textwrap
import requests
import datetime
import sqlite3
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, RichLog, Button
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual import work
from textual.events import Key

# 自動取得版本 (基於檔案修改時間)
try:
    mtime = os.path.getmtime(__file__)
    mod_time = datetime.datetime.fromtimestamp(mtime)
    VERSION = f"v{mod_time.strftime('%Y%m%d.%H%M')}"
except:
    VERSION = "v1.0.0"

# 設定時區
os.environ["TZ"] = "Asia/Taipei"

# 自動偵測 API URL
if os.path.exists("/.dockerenv"):
    API_URL = "http://host.docker.internal:8000/chat"
else:
    API_URL = "http://localhost:8000/chat"

# SQLite 資料庫路徑
DB_PATH = "/home/agent/workspace/history.db"

def init_db():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role: str, content: str):
    """儲存訊息到資料庫"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)', (role, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"儲存訊息失敗: {e}")

def search_similar(query: str, limit: int = 5) -> list:
    """搜尋相似的訊息"""
    if not query or len(query.strip()) < 2:
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 使用 LIKE 進行模糊搜尋
        cursor.execute('''
            SELECT DISTINCT content FROM messages 
            WHERE role = 'user' AND content LIKE ?
            ORDER BY created_at DESC LIMIT ?
        ''', (f'%{query}%', limit))
        results = cursor.fetchall()
        conn.close()
        return [r[0] for r in results]
    except Exception as e:
        print(f"搜尋失敗: {e}")
        return []

# 初始化資料庫
init_db()

class AgentTUI(App):
    """Agent TUI 主應用程式"""
    
    # 設為亮色主題
    DARK = False
    TITLE = f"Agent TUI {VERSION}"
    
    CSS = """
    Screen { background: $surface; }
    #response {
        border: solid $primary;
        height: 65%;
        margin: 1 2;
        padding: 0 1;
        background: $surface;
    }
    #response:focus {
        border: solid $accent;
    }
    #input-container {
        height: auto;
        margin: 1 2;
    }
    #input-wrapper {
        border: solid $secondary;
        height: 3;
    }
    #input {
        width: 100%;
        height: 100%;
        border: none;
    }
    #candidates {
        height: auto;
        max-height: 6;
        border: solid $accent;
        margin: 0 2;
        background: $surface;
    }
    .candidate-item {
        padding: 0 1;
    }
    .candidate-item:hover {
        background: $primary-darken-1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("up", "select_candidate_up", "Up", show=False),
        Binding("down", "select_candidate_down", "Down", show=False),
        Binding("enter", "apply_candidate", "Apply", show=False),
        Binding("escape", "hide_candidates", "Hide", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.candidates = []
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f" Agent 回應 ({VERSION})", id="response-label")
        yield RichLog(id="response", highlight=False, markup=True, auto_scroll=True)
        with Container(id="input-container"):
            with Container(id="input-wrapper"):
                yield Input(placeholder="輸入訊息... (/help 查看指令)", id="input")
            yield Static("", id="candidates")

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()
        r = self.query_one("#response", RichLog)
        tw_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        r.write(f"[bold]Agent TUI {VERSION}[/bold] 已啟動!")
        r.write(f" 台灣時間: {tw_time.strftime('%Y-%m-%d %H:%M:%S')}")
        r.write("輸入訊息開始對話")
        r.write(" 上下鍵選擇歷史記錄候選")
        r.write("-" * 40)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_submit()

    def on_input_changed(self, event: Input.Changed) -> None:
        """輸入變更時搜尋候選"""
        query = event.value.strip()
        if len(query) >= 2:
            self.candidates = search_similar(query)
            self.selected_index = 0  # 預設選中第一個
            self.update_candidates_display()
        else:
            self.candidates = []
            self.selected_index = 0
            self.update_candidates_display()

    def update_candidates_display(self):
        """更新候選顯示"""
        c = self.query_one("#candidates", Static)
        if not self.candidates:
            c.update("")
            return
        
        # 只有一個候選時，自動選中
        if len(self.candidates) == 1:
            self.selected_index = 0
        
        lines = []
        for i, text in enumerate(self.candidates):
            prefix = "▶ " if i == self.selected_index else "  "
            # 截斷過長的文字
            display_text = text[:60] + "..." if len(text) > 60 else text
            lines.append(f"{prefix}{display_text}")
        
        c.update("\n".join(lines))

    def action_select_candidate_up(self) -> None:
        """選擇上一個候選"""
        if len(self.candidates) > 1:
            self.selected_index = (self.selected_index - 1) % len(self.candidates)
            self.update_candidates_display()
        elif len(self.candidates) == 1:
            self.selected_index = 0
            self.update_candidates_display()

    def action_select_candidate_down(self) -> None:
        """選擇下一個候選"""
        if len(self.candidates) > 1:
            self.selected_index = (self.selected_index + 1) % len(self.candidates)
            self.update_candidates_display()
        elif len(self.candidates) == 1:
            self.selected_index = 0
            self.update_candidates_display()

    def action_apply_candidate(self) -> None:
        """套用選中的候選"""
        if self.candidates and self.selected_index < len(self.candidates):
            inp = self.query_one("#input", Input)
            inp.value = self.candidates[self.selected_index]
            self.candidates = []
            self.update_candidates_display()

    def action_hide_candidates(self) -> None:
        """隱藏候選"""
        self.candidates = []
        self.update_candidates_display()

    def action_submit(self) -> None:
        inp = self.query_one("#input", Input)
        msg = inp.value.strip()
        if not msg:
            return
        
        # 儲存使用者輸入到資料庫
        save_message("user", msg)
        
        inp.value = ""
        self.candidates = []
        self.update_candidates_display()
        
        r = self.query_one("#response", RichLog)
        r.write(f"\n[bold]你:[/bold] {msg}")
        r.write("-" * 40)
        self.send_message(msg)

    def render_markdown(self, text: str) -> str:
        """將 Markdown 轉換為 Rich 標記"""
        import re
        
        # 代碼區塊
        text = re.sub(r'```(\w*)\n(.*?)```', r'[dim]```\1\n\2```[/dim]', text, flags=re.DOTALL)
        # 行內代碼
        text = re.sub(r'`([^`]+)`', r'[cyan]`\1`[/cyan]', text)
        # 粗體
        text = re.sub(r'\*\*([^*]+)\*\*', r'[bold]\1[/bold]', text)
        # 斜體
        text = re.sub(r'\*([^*]+)\*', r'[italic]\1[/italic]', text)
        # 標題
        text = re.sub(r'^### (.+)$', r'[bold bright_cyan]\1[/]', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'[bold cyan]\1[/]', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'[bold bright_green]\1[/]', text, flags=re.MULTILINE)
        # 連結
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](underline blue)', text)
        # 列表
        text = re.sub(r'^[-*] (.+)$', r'  • \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\. (.+)$', r'  \g<0>', text, flags=re.MULTILINE)
        
        return text

    @work(exclusive=True, thread=True)
    def send_message(self, message: str) -> None:
        r = self.query_one("#response", RichLog)
        try:
            r.write("[dim]處理中...[/dim]")
            resp = requests.post(API_URL, json={"message": message}, timeout=120)
            if resp.status_code == 200:
                result = resp.json()
                response = result.get("response", "無回應")
                rich_text = self.render_markdown(response)
                r.write(f"[bold]Agent:[/bold] {rich_text}")
                # 儲存 Agent 回應到資料庫
                save_message("assistant", response)
            else:
                r.write(f"[red]錯誤: {resp.status_code}[/red]")
        except Exception as e:
            r.write(f"[red]錯誤: {str(e)}[/red]")
        r.write("-" * 40)

    def action_clear(self) -> None:
        self.query_one("#response", RichLog).clear()

    def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    app = AgentTUI()
    app.run()
