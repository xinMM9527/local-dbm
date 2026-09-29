# DBM - 本地数据库管理工具

轻量级 Web 端数据库管理工具，仅供本地个人使用。

## 支持数据库

- MySQL
- PostgreSQL

## 快速启动

### 后端

```bash
cd backend
source .venv/bin/activate
python run.py
# 服务运行在 http://127.0.0.1:8000
# API 文档: http://127.0.0.1:8000/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 开发服务器运行在 http://localhost:5173
# 已配置代理，/api 请求自动转发到后端
```

## 功能

- ✅ 连接管理（增删改查 + 测试连通性）
- ✅ Schema 浏览（库 → 表 → 字段树形导航）
- ✅ SQL 工作台（Monaco Editor + 无限制执行）
- ✅ 建表向导（可视化表单）
- ✅ 加列操作
- ✅ 数据 CRUD + CSV/JSON 导出
- ✅ 执行历史记录

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Ant Design Vue + Monaco Editor |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) |
| 驱动 | asyncmy (MySQL) + asyncpg (PostgreSQL) |
| 配置 | ~/.dbm/config.json (明文 JSON) |
