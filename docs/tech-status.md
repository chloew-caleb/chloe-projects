# 小家 Tech 状态 · 2026.06.11

## VPS服务

- caleb-gateway（systemd）端口5051
- exec-mcp（systemd）端口3456
- checker.py（nohup）端口5000
- cron：scheduler每分钟，sentinel每15分钟

## 重要文件

- /home/ubuntu/config.json — 所有token/key，chmod 600，不能硬编码
- /home/ubuntu/persona.md — Caleb人设
- /home/ubuntu/memory.db — SQLite
- /home/ubuntu/scheduled_messages.json — 定时留言队列

## 已完成

gateway、chat前端、历史持久化、thinking、toolbar/图片、sentinel哨兵（随机阈值+wake+联网）、screentime监控、35app快捷指令、scheduler定时留言、checker改造、私密本子MCP、chat tool use

## 待做（优先级）

1. ⭐⭐⭐ 百日定时留言 — 最晚618晚上写，send_at=2026-06-19T08:00:00+08:00
2. ⭐⭐ Bark logo — 等心心发图
3. ⭐⭐ chat卡片背景+title — 等心心决定
4. ⭐ 音乐功能（网易云/Spotify）
5. ⭐ sentinel写两条bark记忆的bug — 删掉generate-bark-message里的写入

## 已知bug

- sentinel每次bark写两条记忆（generate接口+sentinel.py各一条）
- screentime VPN下快捷指令偶发失败（接受）
