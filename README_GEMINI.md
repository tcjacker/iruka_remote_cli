# Gemini CLI 集成系统

这个系统允许你通过Web API与Docker容器中的Gemini CLI进行交互。

## 系统架构

```
前端/客户端 → 主服务 (main_service.py) → Agent容器 (agent.py) → Gemini CLI
```

## 功能特性

- 🚀 在Docker容器中运行Gemini CLI
- 🌐 通过REST API与Gemini CLI交互
- 🔄 支持多个隔离的环境
- 📊 实时状态监控
- 🔧 支持重启和错误恢复

## API 端点

### 环境管理

- `POST /environments` - 创建新环境
- `GET /environments` - 列出所有环境
- `DELETE /environments/{env_id}` - 删除环境

### Gemini CLI 交互

- `POST /environments/{env_id}/gemini` - 发送提示到Gemini
- `GET /environments/{env_id}/gemini/status` - 检查Gemini状态
- `POST /environments/{env_id}/gemini/restart` - 重启Gemini CLI

### 通用命令执行

- `POST /environments/{env_id}/execute` - 在环境中执行shell命令

## 使用方法

### 1. 构建Docker镜像

```bash
# 在项目根目录执行
python build_image.py
```

### 2. 启动主服务

```bash
python main_service.py
```

主服务将在端口8080上启动。

### 3. 创建环境并使用Gemini

#### 创建环境
```bash
curl -X POST http://localhost:8080/environments
```

响应示例：
```json
{
  "env_id": "abc123-def456",
  "port": 32768,
  "message": "Environment created successfully"
}
```

#### 发送提示到Gemini
```bash
curl -X POST http://localhost:8080/environments/{env_id}/gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'
```

响应示例：
```json
{
  "response": "Hello! I'm doing well, thank you for asking. How can I help you today?"
}
```

#### 检查Gemini状态
```bash
curl http://localhost:8080/environments/{env_id}/gemini/status
```

#### 重启Gemini CLI
```bash
curl -X POST http://localhost:8080/environments/{env_id}/gemini/restart
```

### 4. 使用测试脚本

```bash
python test_gemini.py
```

## 配置要求

### 环境变量

在使用Gemini CLI之前，你需要设置API密钥：

```bash
export GEMINI_API_KEY="your-api-key-here"
```

或者在Docker容器中设置环境变量。

### Docker要求

- Docker Desktop 或 Docker Engine
- Python 3.9+
- Node.js 18+

## 错误处理

系统包含以下错误处理机制：

1. **连接超时**: Gemini请求超时设置为120秒
2. **自动重启**: 如果Gemini CLI崩溃，可以通过API重启
3. **状态监控**: 实时检查Gemini CLI运行状态
4. **日志记录**: 详细的日志记录用于调试

## 示例代码

### Python客户端示例

```python
import requests

# 创建环境
response = requests.post("http://localhost:8080/environments")
env_id = response.json()["env_id"]

# 发送提示
response = requests.post(
    f"http://localhost:8080/environments/{env_id}/gemini",
    json={"prompt": "What is artificial intelligence?"}
)
print(response.json()["response"])

# 清理
requests.delete(f"http://localhost:8080/environments/{env_id}")
```

### JavaScript客户端示例

```javascript
// 创建环境
const createResponse = await fetch('http://localhost:8080/environments', {
    method: 'POST'
});
const { env_id } = await createResponse.json();

// 发送提示
const geminiResponse = await fetch(`http://localhost:8080/environments/${env_id}/gemini`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: 'Tell me about machine learning' })
});
const result = await geminiResponse.json();
console.log(result.response);

// 清理
await fetch(`http://localhost:8080/environments/${env_id}`, { method: 'DELETE' });
```

## 故障排除

### 常见问题

1. **Gemini CLI无法启动**
   - 检查API密钥是否正确设置
   - 确保网络连接正常
   - 查看容器日志

2. **请求超时**
   - 增加超时时间
   - 检查网络连接
   - 重启Gemini CLI

3. **容器无法创建**
   - 确保Docker正在运行
   - 检查镜像是否正确构建
   - 查看Docker日志

### 日志查看

```bash
# 查看主服务日志
python main_service.py

# 查看Docker容器日志
docker logs <container_id>
```

## 安全注意事项

1. 不要在生产环境中暴露API端点
2. 使用适当的身份验证和授权
3. 定期更新依赖项
4. 监控资源使用情况

## 贡献

欢迎提交问题和改进建议！
