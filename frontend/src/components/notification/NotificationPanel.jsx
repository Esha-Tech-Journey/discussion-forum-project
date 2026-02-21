import { CheckCheck } from 'lucide-react'
import { useNotifications } from '../../context/NotificationsContext'
import { notificationService } from '../../services'
import styles from './NotificationPanel.module.css'

export default function NotificationPanel() {
  const { notifications, markAsRead, markAllAsRead } = useNotifications()

  const handleMarkAsRead = async (notificationId, isRead) => {
    if (!isRead) {
      try {
        await notificationService.markAsRead(notificationId)
        markAsRead(notificationId)
      } catch (err) {
        console.error('Failed to mark notification as read:', err)
      }
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead()
      markAllAsRead()
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h3>Notifications</h3>
        {notifications.some(n => !n.is_read) && (
          <button onClick={handleMarkAllAsRead} className={styles.markAllButton}>
            <CheckCheck size={16} />
            Mark all read
          </button>
        )}
      </div>

      <div className={styles.list}>
        {notifications.length === 0 ? (
          <div className={styles.empty}>
            <p>No notifications</p>
          </div>
        ) : (
          notifications.map(notification => (
            <div
              key={notification.id}
              className={`${styles.item} ${!notification.is_read ? styles.unread : ''}`}
              onClick={() => handleMarkAsRead(notification.id, notification.is_read)}
            >
              <div className={styles.content}>
                <p className={styles.title}>{notification.title}</p>
                <p className={styles.message}>{notification.message}</p>
                <span className={styles.time}>
                  {new Date(notification.created_at).toLocaleDateString()}
                </span>
              </div>
              {!notification.is_read && (
                <div className={styles.unreadIndicator} />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
