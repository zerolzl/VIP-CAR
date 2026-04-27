import api from './index'

export const getAlerts = (params) => api.get('/alerts', { params })
