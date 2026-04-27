import api from './index'

export const getSpots = (params) => api.get('/spots', { params })
export const createSpot = (data) => api.post('/spots', data)
export const updateSpot = (id, data) => api.put(`/spots/${id}`, data)
export const deleteSpot = (id) => api.delete(`/spots/${id}`)
