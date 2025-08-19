# Iruka Remote CLI - 前端

这是 Iruka Remote CLI 项目的前端部分，基于 React + Vite 构建。

## 后端服务器配置

您可以通过环境变量配置后端服务器地址。创建或编辑 `.env` 文件：

```env
# HTTP API 基础 URL
VITE_API_BASE_URL=http://localhost:8000

# WebSocket 基础 URL  
VITE_WS_BASE_URL=ws://localhost:8000
```

## 开发指南

1. 安装依赖：`npm install`
2. 启动开发服务器：`npm run dev`
3. 构建生产版本：`npm run build`

详细配置说明请参考 [CONFIG.md](CONFIG.md)。

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
