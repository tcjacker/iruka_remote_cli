# 已完成的任务

1. [x] 修改后端API模型以支持Claude Code选项
2. [x] 更新项目设置以支持ANTHROPIC_AUTH_TOKEN和ANTHROPIC_BASE_URL
3. [x] 修改Docker环境创建逻辑以支持Claude Code
4. [x] 更新前端UI以支持选择Claude Code或Gemini CLI
5. [x] 修改WebSocket终端连接以支持Claude Code TUI

# 已实施的更改

## 后端更改

### app/api.py
- 更新了Project、ProjectCreate和ProjectSettingsUpdate模型以包含Claude Code的认证令牌字段
- 更新了EnvironmentCreate模型以支持ai_tool字段（默认为"gemini"）
- 修改了create_environment函数以处理Claude Code的认证令牌验证
- 更新了容器名称生成逻辑以支持Claude Code环境
- 更新了容器环境变量设置以支持Claude Code
- 更新了docker_service.create_and_run_environment调用以传递AI工具信息

### app/services.py
- 更新了create_and_run_environment函数签名以接收ai_tool参数
- 修改了setup_script以根据选择安装相应的AI工具（Gemini CLI或Claude CLI）
- 更新了setup_shell_session函数签名以接收ai_tool参数
- 修改了shell启动命令以根据选择启动相应的AI工具

### app/websocket.py
- 更新了websocket_shell函数以检测容器类型（Claude或Gemini）
- 更新了setup_shell_session调用以传递AI工具信息

## 前端更改

### frontend/src/components/ProjectSettings.jsx
- 添加了Anthropic Auth Token和Anthropic Base URL的输入字段
- 更新了handleSave函数以包含Claude Code的设置

### frontend/src/components/NewEnvironmentModal.jsx
- 添加了AI工具选择状态（aiTool）
- 更新了UI以支持选择Claude Code或Gemini CLI
- 更新了handleCreate函数以包含AI工具选择