# Iruka Remote Cli

## 🎯 项目概述

这是一个完整的Docker化Gemini CLI集成系统，通过Web API提供对Google Gemini AI的访问。可以拉取git上代码进行远程代码编写，提交。

## 🏗️ 系统架构

```
前端/客户端 → 主服务(Flask) → Docker容器 → Gemini CLI → Google Gemini AI
```

### 核心组件

1. **主服务** (`main_service.py`) - Flask Web服务，管理Docker容器和API路由
2. **Agent容器** (`agent/`) - 运行Gemini CLI的Docker容器
3. **Gemini CLI** - Google官方的Gemini命令行工具

## ✅ 已实现功能

### 🔧 核心功能
- ✅ Docker容器动态创建和管理
- ✅ Gemini CLI自动安装和配置
- ✅ API密钥安全管理
- ✅ 多环境隔离支持
- ✅ 实时对话交互
- ✅ 容器健康检查
- ✅ 自动清理机制

### 🌐 API端点

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/environments` | 创建新的Docker环境 |
| GET | `/environments/{id}/gemini/status` | 检查Gemini CLI状态 |
| POST | `/environments/{id}/gemini/configure` | 配置API密钥 |
| POST | `/environments/{id}/gemini` | 发送提示到Gemini |
| POST | `/environments/{id}/gemini/restart` | 重启Gemini CLI |
| DELETE | `/environments/{id}` | 删除环境 |

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd /Users/tc/ai/auto_cli

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 启动主服务
python main_service.py
```

服务将在 `http://127.0.0.1:8080` 启动

### 3. 获取API密钥

访问 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取Gemini API密钥

### 4. 使用示例

#### 创建环境
```bash
curl -X POST http://127.0.0.1:8080/environments
```

#### 配置API密钥
```bash
curl -X POST http://127.0.0.1:8080/environments/{ENV_ID}/gemini/configure \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY"}'
```

#### 发送提示（配置API密钥后无需再传入）
```bash
curl -X POST http://127.0.0.1:8080/environments/{ENV_ID}/gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, what is Python?"}'
```

#### 可选：在请求中覆盖API密钥
```bash
curl -X POST http://127.0.0.1:8080/environments/{ENV_ID}/gemini \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, what is Python?", "api_key": "DIFFERENT_API_KEY"}'
```

## 🧪 测试脚本

### 完整功能演示
```bash
python demo_gemini_system.py
```

### API密钥测试
```bash
python test_gemini_with_api.py
```

## 📁 项目结构

```
auto_cli/
├── main_service.py              # 主服务Flask应用
├── agent/
│   ├── Dockerfile              # Agent容器镜像定义
│   ├── agent.py                # Agent服务代码
│   ├── startup.sh              # 容器启动脚本
│   └── requirements.txt        # Python依赖
├── demo_gemini_system.py       # 完整演示脚本
├── test_gemini_with_api.py     # API测试脚本
├── README_FINAL.md             # 项目文档
└── venv/                       # Python虚拟环境
```

## 🔍 技术细节

### Docker镜像构建
```bash
# 设置代理（如需要）
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7890

# 构建镜像
docker build -t agent-service:latest ./agent
```

### 容器启动流程
1. 安装Node.js和npm
2. 安装Gemini CLI (`npm install -g @google/gemini-cli`)
3. 启动Python Flask服务
4. 暴露端口5000供外部访问

### API密钥管理
- 支持环境变量 `GEMINI_API_KEY`
- 支持配置文件 `~/.gemini/settings.json`
- 支持请求中传递API密钥（可覆盖已配置的密钥）
- **新功能**：配置后API密钥自动持久化，后续请求无需重复传入

## 🛠️ 故障排查

### 常见问题

1. **容器启动慢**
   - Gemini CLI安装需要时间，首次启动约60-90秒
   - 检查网络连接和npm镜像源

2. **API密钥错误**
   - 确保API密钥有效
   - 检查API密钥权限设置

3. **端口冲突**
   - 系统自动分配端口，避免冲突
   - 检查防火墙设置

### 调试命令

```bash
# 查看容器状态
docker ps

# 查看容器日志
docker logs <CONTAINER_ID>

# 测试容器健康
curl http://127.0.0.1:<PORT>/health

# 检查Gemini状态
curl http://127.0.0.1:<PORT>/gemini/status
```

## 🔐 安全考虑

- API密钥通过HTTPS传输（生产环境）
- 容器间网络隔离
- 自动清理临时文件
- 限制容器资源使用

## 📈 性能优化

- 容器复用机制
- 连接池管理
- 请求超时控制
- 内存使用监控

## 🚀 部署建议

### 生产环境
1. 使用HTTPS
2. 配置反向代理（Nginx）
3. 设置容器资源限制
4. 启用日志轮转
5. 配置监控告警

### 扩展性
- 支持多实例部署
- 可集成负载均衡
- 支持容器编排（Kubernetes）

## 📝 更新日志

### v1.0 (当前版本)
- ✅ 完整的Docker集成
- ✅ Gemini CLI自动安装
- ✅ Web API接口
- ✅ 多环境支持
- ✅ API密钥管理
- ✅ 健康检查机制

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

GPL-3.0 license

## 📞 支持

如有问题，请创建Issue或联系维护者（tcjack@126.com）。

---

**🎉 恭喜！你现在拥有一个完整的Gemini CLI Docker集成系统！**
