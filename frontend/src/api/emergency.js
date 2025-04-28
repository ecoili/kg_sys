import { api } from './auth' // 使用命名导入



// 模拟特情
export const simulateEmergency = async (data) => {
  return await api.post('/emergency/simulate', data)
  // 不需要额外try-catch，因为错误已在拦截器统一处理
}

// 其他emergency相关API可以按照相同模式添加
// 其他emergency相关API
export const getEmergencyList = async (params) => {
  return await api.get('/emergency/list', { params })
}

export const updateEmergencyStatus = async (id, status) => {
  return await api.patch(`/emergency/${id}/status`, { status })
}