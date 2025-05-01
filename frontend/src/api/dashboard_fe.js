import { api } from './auth'



export const fetchPositions = async () => {
  return await api.get('/getpositions')
}

export const fetchTasks = async () => {
  return await api.get('/gettasks')
}