import axios from 'axios';
import router from "@/router";
const api = axios.create({
  baseURL: '/api', // Flask 后端地址
});
// 封装与后端flask的认证相关api请求，集中管理api端点，便于维护

// 请求拦截器：自动添加Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理Token过期
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response.status === 401 && !error.config._retry) {
      // 尝试刷新Token
      return refreshTokenAndRetry(error);
    }
    return Promise.reject(error);
  }
);

async function refreshTokenAndRetry(error) {
  error.config._retry = true;
  try {
    const newToken = await refreshToken();
    localStorage.setItem('access_token', newToken);
    error.config.headers.Authorization = `Bearer ${newToken}`;
    return api(error.config);
  } catch (e) {
    // 刷新失败，跳转登录
    await router.push('/auth/login');
    return Promise.reject(e);
  }
}
// 刷新逻辑
export const refreshToken = async () => {
    try {
        const { data } = await api.post('/auth/refresh');
        return data.access_token;
    } catch (error) {
        console.error('刷新Token失败:', error);
        throw error; // 抛出错误供调用方处理
    }
};

// 获取验证码
export const getCaptcha = async () => {
  return api.get('/auth/captcha');
};


// 用户注册
export const register = (data) => {
  return api.post('/auth/register', data);
};

// 用户登录
export const login = async (loginData) => {
  try {
    const response = await api.post('/auth/login', loginData);

    // 存储Token和用户信息
    localStorage.setItem('access_token', response.access_token);
    // localStorage.setItem('user_info', JSON.stringify(response.user_info));

    return response;
  } catch (error) {
    throw error.response.data;  // 抛出错误信息供组件处理
  }
};

// 忘记密码
export const forgotPassword = (phone) => {
  return api.post('/auth/forgot-password', { phone });
};

// 重置密码
export const resetPassword = (data) => {
  return api.post('/auth/reset-password', data);
};