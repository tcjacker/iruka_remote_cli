// API 配置管理
const getApiConfig = () => {
  // 从环境变量获取配置，如果没有则使用默认值
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

  return {
    apiBaseUrl,
    wsBaseUrl,
    // 便捷方法来构建 API URL
    buildApiUrl: (path) => `${apiBaseUrl}${path}`,
    // 便捷方法来构建 WebSocket URL
    buildWsUrl: (path) => `${wsBaseUrl}${path}`,
  };
};

const apiConfig = getApiConfig();

export const checkRegistrationStatus = async () => {
  const response = await fetch(`${apiConfig.buildApiUrl('/api/auth/check_register')}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.json();
};

export default apiConfig;
