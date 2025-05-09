import { api } from './auth' // 使用命名导入



// 模拟特情
export const simulateEmergency = async (data) => {
  return await api.post('/emergency/simulate', data)
  // 不需要额外try-catch，因为错误已在拦截器统一处理
}

export const simulateEmergency2 = async (data) => {
  return await api.post('/simulate/test', data)
  // 不需要额外try-catch，因为错误已在拦截器统一处理
}
export const simulateEmergency3 = async (data) => {
  return await api.post('/simulateEmerg', data)
  // 不需要额外try-catch，因为错误已在拦截器统一处理
}

// export const simulateMultitaskEmergency = async (data) => {
//   return await api.post('/simulateMultiEmerg', data)
//   // 不需要额外try-catch，因为错误已在拦截器统一处理
// }

export const simulateMultitaskEmergency = async (data) => {
  return await api.post('/simulateMultiEmerg', {
    position_ids: Array.isArray(data.position_ids) ? data.position_ids : [data.position_ids],
    event_types: Array.isArray(data.event_types) ? data.event_types : [data.event_types],
    severities: Array.isArray(data.severities) ? data.severities : [data.severities],
    durations: Array.isArray(data.durations) ? data.durations : [data.durations]
  })
}

// 其他emergency相关API可以按照相同模式添加
// 其他emergency相关API
export const getEmergencyList = async (params) => {
  return await api.get('/emergency/list', { params })
}

export const updateEmergencyStatus = async (id, status) => {
  return await api.patch(`/emergency/${id}/status`, { status })
}