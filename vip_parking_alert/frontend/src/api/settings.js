import api from './index'

export const getExternalDb = () => api.get('/settings/external-db')
export const updateExternalDb = (data) => api.put('/settings/external-db', data)
export const testExternalDb = () => api.post('/settings/external-db/test')
export const getSmsGateway = () => api.get('/settings/sms-gateway')
export const updateSmsGateway = (data) => api.put('/settings/sms-gateway', data)
export const reloadConfig = () => api.post('/system/reload-config')
export const getHealth = () => api.get('/system/health')
