# Docker 開發環境 Skill

## 用途
管理 Docker 容器內的開發流程，包括：
- 程式碼修改後的 Commit
- 還原到前一個版本
- 查看 Git 狀態
- 推送到 GitHub

## 使用方式

### 1. 查看 Git 狀態
```bash
cd /c/Users/HCH/dev-agent-container
git status
git diff
git log --oneline -5
```

### 2. Commit 變更
```bash
cd /c/Users/HCH/dev-agent-container

# 查看變更
git status
git diff

# 添加變更的檔案
git add -A

# 提交 (注意：不要 commit history.db)
git reset HEAD workspace/history.db 2>/dev/null

# 撰寫 commit 訊息
git commit -m "your commit message"

# 推送到 GitHub
git push
```

### 3. 還原到前一個版本
```bash
cd /c/Users/HCH/dev-agent-container

# 查看 commit 歷史
git log --oneline

# 還原到前一個版本 (用 commit hash)
git reset --hard <commit-hash>

# 強制推送到 GitHub
git push --force
```

### 4. 恢復被刪除的歷史 (如果 --force push 失敗)
```bash
git reflog
git reset --hard <想要恢復的 commit>
```

## 注意事項

1. **不要 commit history.db** - 這是本地對話資料庫
   - 每次 commit 前都要執行：`git reset HEAD workspace/history.db`

2. **先還原再 commit** - 如果不小心 commit 了不需要的檔案：
   ```bash
   git reset --soft HEAD~1
   git reset HEAD <不要的檔案>
   git checkout -- <不要的檔案>
   git commit -m "修正"
   ```

3. **確認後再 force push** - `--force` 會覆蓋遠端歷史

## 常用指令速查

| 動作 | 指令 |
|------|------|
| 查看狀態 | `git status` |
| 查看差異 | `git diff` |
| 查看歷史 | `git log --oneline -5` |
| 添加檔案 | `git add -A` |
| 提交變更 | `git commit -m "訊息"` |
| 推送 | `git push` |
| 還原版本 | `git reset --hard <hash>` |
| 強制推送 | `git push --force` |
