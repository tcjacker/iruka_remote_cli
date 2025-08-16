# Claude 聊天记录持久化修复

## 问题描述

之前每次切换环境后，Claude CLI 的聊天记录会丢失，用户需要重新开始对话。这是因为：

1. **容器级别隔离**：每个环境运行在独立的 Docker 容器中
2. **无持久化存储**：Claude CLI 会话数据存储在容器内存中
3. **会话重新初始化**：每次连接都会启动新的 Claude CLI 进程

## 解决方案

### 1. 持久化目录结构

在每个 Claude 环境中创建持久化目录：
```
/workspace/.ai_data/claude/  # Claude 会话数据存储目录
/root/.config/claude/        # Claude 配置文件目录
```

### 2. Claude CLI 配置

自动配置 Claude CLI 使用持久化存储：
```json
{
  "dataDir": "/workspace/.ai_data/claude",
  "persistentSessions": true,
  "sessionTimeout": 86400000
}
```

### 3. 环境变量设置

设置以下环境变量确保 Claude CLI 使用持久化配置：
- `CLAUDE_DATA_DIR="/workspace/.ai_data/claude"`
- `CLAUDE_CONFIG_DIR="/root/.config/claude"`

### 4. 数据库会话管理

在项目数据库中为每个环境添加会话管理字段：
```json
{
  "session_data": {
    "created_at": "2025-01-16T21:20:00Z",
    "last_active": "2025-01-16T21:25:00Z",
    "session_id": "uuid-string",
    "persistent_data_path": "/workspace/.ai_data/claude",
    "persistent_files_count": 5,
    "data_last_modified": "2025-01-16T21:25:00Z"
  }
}
```

## 新增 API 接口

### 1. 获取会话信息
```
GET /projects/{project_name}/environments/{env_id}/session
```
返回 Claude 环境的会话详细信息，包括持久化文件数量和最后修改时间。

### 2. 重置会话数据
```
POST /projects/{project_name}/environments/{env_id}/session/reset
```
清空 Claude 会话数据，重新开始对话。

### 3. 环境状态（增强）
```
GET /projects/{project_name}/environments/{env_id}/status
```
现在返回的状态信息中包含会话数据。

## 修改的文件

### 1. `backend/app/services.py`
- 在容器创建脚本中添加持久化目录创建
- 配置 Claude CLI 使用持久化存储
- 在 shell 启动时设置环境变量
- 添加会话数据更新机制

### 2. `backend/app/api.py`
- 扩展 Environment 模型，添加 session_data 字段
- 更新环境创建逻辑，初始化会话数据
- 添加会话管理 API 接口

## 使用方法

### 1. 创建新的 Claude 环境
创建环境时会自动配置持久化存储，无需额外操作。

### 2. 查看会话信息
```bash
curl -X GET "http://localhost:8000/projects/my-project/environments/my-env/session" \
  -H "Authorization: Bearer your-token"
```

### 3. 重置会话（如需要）
```bash
curl -X POST "http://localhost:8000/projects/my-project/environments/my-env/session/reset" \
  -H "Authorization: Bearer your-token"
```

## 预期效果

1. **聊天记录保持**：切换环境后再次连接，之前的对话历史会保留
2. **会话连续性**：Claude CLI 能够记住上下文和对话状态
3. **数据可视化**：通过 API 可以查看会话统计信息
4. **灵活管理**：可以选择性重置会话数据

## 注意事项

1. **仅适用于新创建的环境**：现有环境需要重新创建才能享受持久化功能
2. **存储空间**：持久化数据会占用容器存储空间，长期使用建议定期清理
3. **Claude CLI 版本**：确保使用支持持久化配置的 Claude CLI 版本

## 测试建议

1. 创建新的 Claude 环境
2. 进行一段对话
3. 切换到其他环境
4. 再次回到原环境，验证对话历史是否保留
5. 使用 API 接口查看会话信息
