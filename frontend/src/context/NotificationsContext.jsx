import { createContext, useState, useContext, useCallback } from 'react'

const NotificationsContext = createContext(null)

const dedupeById = (items) => {
  const seen = new Set()
  const out = []
  for (const item of (Array.isArray(items) ? items : [])) {
    const id = item?.id
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(item)
  }
  return out
}

export const NotificationsProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showPanel, setShowPanel] = useState(false)

  const addNotification = useCallback((notification) => {
    if (!notification?.id) {
      return
    }

    setNotifications(prev => {
      if (prev.some((n) => n?.id === notification.id)) {
        return prev
      }
      return [notification, ...prev]
    })

    if (!notification.is_read) {
      setUnreadCount(prev => prev + 1)
    }
  }, [])

  const markAsRead = useCallback((notificationId) => {
    setNotifications(prev =>
      prev.map(n =>
        n.id === notificationId ? { ...n, is_read: true } : n
      )
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, is_read: true }))
    )
    setUnreadCount(0)
  }, [])

  const setNotificationsList = useCallback((list) => {
    const next = dedupeById(list)
    setNotifications(next)
    const unread = next.filter(n => !n.is_read).length
    setUnreadCount(unread)
  }, [])

  const removeNotification = useCallback((notificationId) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId))
  }, [])

  const value = {
    notifications,
    unreadCount,
    showPanel,
    setShowPanel,
    addNotification,
    markAsRead,
    markAllAsRead,
    setNotificationsList,
    removeNotification,
  }

  return (
    <NotificationsContext.Provider value={value}>
      {children}
    </NotificationsContext.Provider>
  )
}

export const useNotifications = () => {
  const context = useContext(NotificationsContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationsProvider')
  }
  return context
}
