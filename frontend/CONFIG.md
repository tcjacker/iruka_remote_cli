# 前端配置说明

## 后端服务器配置

您可以通过以下方式配置后端服务器地址：

### 方法1：环境变量（推荐）

创建 `.env` 文件在项目根目录下：

```env
# HTTP API 基础 URL
VITE_API_BASE_URL=http://your-backend-server:8000

# WebSocket 基础 URL  
VITE_WS_BASE_URL=ws://your-backend-server:8000
```

### 方法2：直接修改配置文件

编辑 `src/config/api.js` 文件，修改默认值：

```javascript
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://your-backend-server:8000';
const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://your-backend-server:8000';
```

## 示例配置

- 本地开发：`http://localhost:8000`
- 远程服务器：`http://192.168.1.100:8000`
- 域名：`https://api.yourdomain.com`

## 注意事项

- 修改配置后需要重新启动开发服务器
- 生产环境部署时请确保环境变量正确设置
- WebSocket URL 的协议应与 HTTP URL 对应（http -> ws, https -> wss）
