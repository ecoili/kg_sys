import { api } from './auth'



export const fetchPositions = async () => {
  return await api.get('/getpositions')
}

export const fetchTasks = async () => {
  return await api.get('/gettasks')
}

export const fetchPosRelations = async () => {
  return await api.get('/getpositionrelations')
}

export const fetchPosTaskRelations = async () => {
  return await api.get('/getpositiontaskrelations')
}

export const fetchTasksByPositionId = async (positionId) => {
  return await api.get(`/gettasksbypositionid/${positionId}`);
}
// 任务信息界面相关api
export const addTask = async (taskData) => {
  return await api.post('/task', taskData);
}

export const deleteTask = async (taskId) => {
  return await api.delete(`/task/${taskId}`);
}

export const updateTask = async (taskId, updateData) => {
  return await api.put(`/task/${taskId}`, updateData);
}

export const assignTaskToPosition = async (taskId, positionId) => {
  return await api.post(`/task/${taskId}/assign/${positionId}`);
}

// 阵位信息界面相关api
export const addPosition = async (positionData) => {
  return await api.post('/position', positionData);
}

export const updatePosition = async (positionId, updateData) => {
  return await api.put(`/position/${positionId}`, updateData);
}

export const deletePosition = async (positionId) => {
  return await api.delete(`/position/${positionId}`);
}

export const getPositionRelations = async (positionId) => {
  return await api.get(`/position/${positionId}/relations`);
}

export const getPositionTaskRelations = async (positionId) => {
  return await api.get(`/position/${positionId}/taskrelations`);
}


export const checkPosition = async (positionData) => {
  return await api.post('/checkposition', positionData);
}

export const checkPositionExc = async (positionData) => {
  return await api.post('/checkpositionexc', positionData);
}

export const checkRelation = async (sourceId, targetId, type) => {
  return await api.get('/checkrelation', {
    params: { sourceId, targetId, type }
  })
}

export const addRelation = async (relationData) => {
  return await api.post('/addrelation', relationData)
}

export const deleteRelation = async (sourceId, targetId, type) => {
  return await api.delete('/deleterelation', {
    data: { sourceId, targetId, type }
  })
}

// 删除任务分配关系
export const deleteTaskAssignment = async (taskId, positionId) => {
  return await api.delete(`/task/${taskId}/unassign/${positionId}`);
}