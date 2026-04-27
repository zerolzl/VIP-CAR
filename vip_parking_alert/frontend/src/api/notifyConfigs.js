import api from './index'

export const getNotifyConfigs = (spotId) => api.get(`/spots/${spotId}/notify-configs`)
export const createNotifyConfig = (spotId, data) => api.post(`/spots/${spotId}/notify-configs`, data)
export const updateNotifyConfig = (id, data) => api.put(`/notify-configs/${id}`, data)
export const deleteNotifyConfig = (id) => api.delete(`/notify-configs/${id}`)
