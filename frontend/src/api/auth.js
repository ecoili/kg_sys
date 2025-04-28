import axios from 'axios';
import router from "@/router";

export const api = axios.create({
  baseURL: '/api', // Flask 后端地址
})
// 封装与后端flask的认证相关api请求，集中管理api端点，便于维护

// 请求拦截器：自动添加Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config
})

// 响应拦截器：处理Token过期
api.interceptors.response.use(
    response => {
        console.log("进入响应拦截器")
        console.log('Axios response:', response)
    // 统一处理成功响应
     const { data } = response
  // 统一提取业务数据（兼容有无 data 包裹的情况）
  const businessData = data.data ?? data

  // 可选：检查错误码（如 code != 200 时抛出异常）
  if (data.code && data.code !== 200) {
    return Promise.reject(data)
  }
  return businessData
  },
  error => {
      console.error('Axios error:', error)
      const apiError = {
      code: error.response?.status || 500,
      message: error.response?.data?.message || '网络错误',
      errors: error.response?.data?.errors || []
    }
    console.error('API Error:', apiError)
      //401处理
      if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      // router.push('/auth/login')
    }
    return Promise.reject(apiError)
  }
)

async function refreshTokenAndRetry(error) {
  error.config._retry = true;
  try {
    const newToken = await refreshToken();
    localStorage.setItem('access_token', newToken);
    error.config.headers.Authorization = `Bearer ${newToken}`;
    return api(error.config);
  } catch (e) {
    // 刷新失败，清除旧Token，跳转登录
    localStorage.removeItem('access_token');
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
  /*const { data } = await api.get('/auth/captcha');
  return {
    image: data.image,
    captcha_id: data.captcha_id*/
    return await api.get('/auth/captcha') // 已经是解构后的业务数据

}


// 用户注册
export const register = (data) => {
  return api.post('/auth/register', data);
};

// 用户登录
export const login = async (loginData) => {
  try {
    /*const response = await api.post('/auth/login', loginData);

    // 存储登录Token
    localStorage.setItem('access_token', response.access_token);
    // localStorage.setItem('user_info', JSON.stringify(response.user_info));

    return response*/
      console.log("进入登录方法")
    /*// 解构出data，flask默认返回数据在data中
    const { data } = await api.post('/auth/login', loginData)
    localStorage.setItem('access_token', data.access_token)
    return data // 返回完整响应数据供组件使用*/
      return await api.post('/auth/login', loginData) // 已经是解构后的业务数据
      } catch (error) {
      throw error // 错误已在拦截器处理
  }
}

// 忘记密码
export const forgotPassword = (phone) => {
  return api.post('/auth/forgot-password', { phone });
};

// 重置密码
export const resetPassword = (data) => {
  return api.post('/auth/reset-password', data);
};