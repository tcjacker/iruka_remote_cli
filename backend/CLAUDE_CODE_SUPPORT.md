# Iruka Remote CLI - Claude Code 支持

这个项目现在支持使用Claude Code，除了原有的Gemini CLI支持。Claude Code CLI工具会自动安装到Docker环境中。

## 新增功能

1. **Claude Code 支持**：用户现在可以选择在创建环境时使用Claude Code而不是Gemini CLI（Claude Code是一个网页版工具）
2. **双AI工具支持**：项目可以同时配置Gemini和Claude的认证令牌
3. **灵活的环境配置**：每个环境可以独立选择使用Gemini CLI或Claude Code

## 环境变量

当选择Claude Code时，以下环境变量将被注入到Docker容器中：
- `ANTHROPIC_AUTH_TOKEN`：Anthropic认证令牌
- `ANTHROPIC_BASE_URL`：Anthropic API基础URL
- `GIT_TOKEN`：Git访问令牌

当选择Gemini CLI时，以下环境变量将被注入到Docker容器中：
- `GEMINI_API_KEY`：Gemini API密钥
- `GIT_TOKEN`：Git访问令牌

## 使用方法

1. 在项目设置中配置Anthropic Auth Token和Anthropic Base URL
2. 创建新环境时选择"Claude Code"作为AI工具
3. 环境将自动安装 Claude Code CLI 并启动 Claude TUI