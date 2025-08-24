# 功能实现：断开连接后自动停止 Docker 容器

为了在用户断开 WebSocket 连接 5 分钟后自动停止对应的 Docker 容器以节省资源，我们对后端代码进行了以下修改。

## 1. `backend/app/main.py`

**核心改动：添加了后台清理任务。**

- **导入必要的模块**：引入了 `asyncio`, `time`, `BackgroundTasks` 以及 `project_service` 和 `docker_service`。
- **创建后台任务 `cleanup_inactive_environments`**：
    - 这是一个无限循环的异步函数，每 60 秒运行一次。
    - 它会获取所有项目，并遍历其中每个环境。
    - 如果一个环境的状态是 "running" 并且记录了 `disconnected_at` 时间戳，任务会计算其非活跃时间。
    - 如果非活跃时间超过 300 秒（5分钟），任务会：
        1.  根据环境的 AI 工具类型（gemini 或 claude）构建正确的容器名称。
        2.  调用 `docker_service.stop_container()` 来停止对应的 Docker 容器。
        3.  调用 `project_service.update_environment_status()` 将环境状态更新为 "stopped"，并清除 `disconnected_at` 时间戳。
- **注册启动事件**：
    - 使用 `@app.on_event("startup")` 装饰器，在 FastAPI 应用启动时，自动在后台创建并运行 `cleanup_inactive_environments` 任务。

## 2. `backend/app/services.py`

**核心改动：增强了服务层能力，以支持状态更新和更健壮的容器操作。**

- **`ProjectService` 中新增方法**：
    - 添加了 `update_environment_status(project_name, env_id, updates)` 方法。
    - 此方法允许精确更新指定项目中特定环境的字段（例如 `status` 或 `disconnected_at`），并将更改持久化到 `db.json`。
- **`DockerService` 中修改方法**：
    - 增强了 `stop_container` 和 `remove_container` 方法的健壮性。
    - 现在，如果尝试停止或移除一个不存在的容器，这些方法将打印一条消息而不是抛出 `NotFound` 异常，这确保了后台清理任务不会因容器已被手动删除等情况而崩溃。

## 3. `backend/app/websocket.py`

**核心改动：在 WebSocket 的连接和断开事件中记录时间戳。**

- **连接成功时**：
    - 在 `websocket_shell` 函数中，当一个 WebSocket 连接成功建立并通过身份验证后，会立即调用 `project_service.update_environment_status`。
    - 此调用会将对应环境的 `disconnected_at` 字段设置为 `None`，表示当前有活跃的连接。
- **连接断开时**：
    - 在 `websocket_shell` 函数的 `finally` 代码块中（此代码块在连接关闭时总会执行），会再次调用 `project_service.update_environment_status`。
    - 这一次调用会将 `disconnected_at` 字段设置为当前的服务器时间戳 (`time.time()`)，从而精确记录连接断开的时间点，以便后台任务进行判断。
