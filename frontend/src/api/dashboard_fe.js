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
