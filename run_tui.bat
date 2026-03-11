@echo off
echo Starting Agent TUI...
echo.
docker exec -it dev-agent python3 /home/agent/workspace/agent_tui.py
pause
