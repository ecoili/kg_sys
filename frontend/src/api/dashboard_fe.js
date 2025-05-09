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
