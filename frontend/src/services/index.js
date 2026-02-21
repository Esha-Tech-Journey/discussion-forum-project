import apiClient from './apiClient'

export const authService = {
  register: (email, password) =>
    apiClient.post('/auth/register', { email, password }),

  login: (email, password) =>
    apiClient.post('/auth/login', { email, password }),

  refresh: (refreshToken) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),

  me: () => apiClient.get('/auth/me'),

  updateProfile: (data) =>
    apiClient.put('/auth/me', data),

  changePassword: (email, oldPassword, newPassword) =>
    apiClient.post('/auth/change-password', {
      email,
      old_password: oldPassword,
      new_password: newPassword,
    }),
}

export const threadService = {
  getThreads: (page = 1, size = 10, tags = null) =>
    apiClient.get('/threads', {
      params: { page, size, tags: tags?.join(',') },
    }),

  getThread: (threadId) => apiClient.get(`/threads/${threadId}`),

  createThread: (data) =>
    apiClient.post('/threads', data),

  updateThread: (threadId, data) =>
    apiClient.put(`/threads/${threadId}`, data),

  deleteThread: (threadId) =>
    apiClient.delete(`/threads/${threadId}`),
}

export const commentService = {
  getComments: (threadId, page = 1, size = 50) =>
    apiClient.get(`/comments/thread/${threadId}`, { params: { page, size } }),

  getComment: (commentId) =>
    apiClient.get(`/comments/${commentId}`),

  createComment: (data) =>
    apiClient.post('/comments', data),

  updateComment: (commentId, data) =>
    apiClient.put(`/comments/${commentId}`, data),

  deleteComment: (commentId) =>
    apiClient.delete(`/comments/${commentId}`),
}

export const likeService = {
  likeThread: (threadId) =>
    apiClient.post(`/likes`, { thread_id: threadId }),

  unlikeThread: (threadId) =>
    apiClient.delete(`/likes`, {
      data: { thread_id: threadId },
    }),

  likeComment: (commentId) =>
    apiClient.post(`/likes`, { comment_id: commentId }),

  unlikeComment: (commentId) =>
    apiClient.delete(`/likes`, {
      data: { comment_id: commentId },
    }),
}

export const notificationService = {
  getNotifications: (page = 1, size = 10) =>
    apiClient.get('/notifications', { params: { page, size } }),

  getUnreadCount: () =>
    apiClient.get('/notifications/unread-count'),

  markAsRead: (notificationId) =>
    apiClient.patch(`/notifications/${notificationId}/read`),

  markAllAsRead: () =>
    apiClient.patch('/notifications/read-all'),
}

export const searchService = {
  searchThreads: (query, page = 1, size = 10, searchIn = 'all', sortBy = 'relevance') =>
    apiClient.get('/search/threads', {
      params: { q: query, page, size, searchIn, sortBy },
    }),
}

export const moderationService = {
  getReviews: (page = 1, size = 10, status = null) =>
    apiClient.get(
      status === 'completed' ? '/moderation/completed' : '/moderation/pending',
      { params: { page, size } },
    ),

  getReview: (reviewId) =>
    apiClient.get(`/moderation/${reviewId}`),

  takeAction: (reviewId, data) =>
    apiClient.post(`/moderation/${reviewId}/action`, data),

  markReviewCompleted: (reviewId) =>
    apiClient.post(`/moderation/${reviewId}/action`, { status: 'COMPLETED' }),
}

export const userService = {
  getProfile: () => apiClient.get('/users/me'),
  getUsers: (page = 1, size = 10, q = '') =>
    apiClient.get('/users', { params: { page, size, q: q || undefined } }),
  suggestUsers: (q = '', limit = 8) =>
    apiClient.get('/users/suggest', { params: { q: q || undefined, limit } }),
  getUserActivity: (userId, limitThreads = 10, limitComments = 10, limitLikes = 10) =>
    apiClient.get(`/users/${userId}/activity`, {
      params: {
        limit_threads: limitThreads,
        limit_comments: limitComments,
        limit_likes: limitLikes,
      },
    }),
  getUsersByRoleStats: (roleName, page = 1, size = 10, q = '') =>
    apiClient.get('/users/role-stats', {
      params: { role_name: roleName, page, size, q: q || undefined },
    }),
  updateUser: (userId, data) =>
    apiClient.put(`/users/${userId}`, data),
  changeRole: (userId, roleName) =>
    apiClient.post(`/users/${userId}/roles`, { role_name: roleName }),
}

export const mentionService = {
  getMentions: (page = 1, size = 10) =>
    apiClient.get('/mentions', { params: { page, size } }),
}
