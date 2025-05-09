import { api } from './auth'

// 获取用户信息
export const getUserInfo = async () => {
    return await api.get('/get-userinfo')
}

// 更新用户名
export const updateUsername = async (username) => {
    return await api.put('/update-username', { username })
}

// 更新密码
export const updatePassword = async (currentPassword, newPassword) => {
    return await api.put('/update-password', {
        currentPassword,
        newPassword
    })
}

// 获取用户头像
export const getAvatar = async () => {
    return await api.get('/get-avatar')
}

// 更新用户头像
export const updateAvatar = async (avatarUrl) => {
    return await api.post('/update-avatar', { avatar: avatarUrl })
}