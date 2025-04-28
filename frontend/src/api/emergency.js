import { api } from './auth'; // 使用命名导入



// 模拟特情
export const simulateEmergency = async (data) => {
  try {
    return await api.post('/emergency/simulate', data); // 使用统一的api实例
  } catch (error) {
    throw error // 错误已在拦截器处理
  }
}

// 其他emergency相关API可以按照相同模式添加