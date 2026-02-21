import { Link, useLocation } from 'react-router-dom'
import { Menu, LogOut, User, Bell } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useNotifications } from '../../context/NotificationsContext'
import { NotificationPanel } from '../notification'
import { SearchBar } from '../common'
import styles from './Header.module.css'
import { useEffect } from 'react'
import { notificationService } from '../../services'
import { wsManager } from '../../services/websocket'

export default function Header({ onMenuClick }) {
  const location = useLocation()
  const { user, logout, isAuthenticated } = useAuth()
  const { unreadCount, setNotificationsList, showPanel, setShowPanel, addNotification } = useNotifications()
  const displayName = user?.name?.trim() || user?.email?.split('@')?.[0] || 'User'
  const avatarFallback = displayName.charAt(0).toUpperCase()
  const roleNames = (user?.roles || []).map((role) => role.role_name || role.name || role)
  const dashboardLink = roleNames.includes('ADMIN')
    ? '/dashboard/admin'
    : roleNames.includes('MODERATOR')
      ? '/dashboard/moderator'
      : '/dashboard/member'

  useEffect(() => {
    if (isAuthenticated) {
      loadNotifications()
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (!isAuthenticated) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    wsManager.connect(token)
    const unsubscribeNotification = wsManager.on('notification', (payload) => {
      addNotification(payload)
    })
    const unsubscribeUser = wsManager.on('user', (payload) => {
      const targetUser = payload?.user
      if (!targetUser || Number(targetUser.id) !== Number(user?.id)) {
        return
      }
      if (targetUser.is_active === false) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        logout()
        alert('Your account has been deactivated by admin.')
        window.location.href = '/login'
      }
    })

    return () => {
      unsubscribeNotification()
      unsubscribeUser()
    }
  }, [isAuthenticated, addNotification, user?.id, logout])

  const loadNotifications = async () => {
    try {
      const response = await notificationService.getNotifications(1, 10)
      setNotificationsList(response.data.items || [])
    } catch (err) {
      console.error('Failed to load notifications:', err)
    }
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.left}>
          <button className={styles.menuButton} onClick={onMenuClick}>
            <Menu size={24} />
          </button>
          <Link to="/threads" className={styles.logo}>
            Forum
          </Link>
          {isAuthenticated && (
            <div className={styles.welcome}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt={displayName} className={styles.avatar} />
              ) : (
                <div className={styles.avatarFallback}>{avatarFallback}</div>
              )}
              <div className={styles.welcomeText}>
                <span className={styles.welcomeLabel}>Welcome</span>
                <strong className={styles.welcomeName}>{displayName}</strong>
              </div>
            </div>
          )}
        </div>

        <div className={styles.center}>
          {location.pathname === '/threads' && <SearchBar />}
        </div>

        <div className={styles.right}>
          {isAuthenticated ? (
            <>
              <div className={styles.notificationBell}>
                <button
                  onClick={() => setShowPanel(!showPanel)}
                  className={styles.bellButton}
                >
                  <Bell size={20} />
                  {unreadCount > 0 && (
                    <span className={styles.badge}>{unreadCount}</span>
                  )}
                </button>
                {showPanel && <NotificationPanel onClose={() => setShowPanel(false)} />}
              </div>

              <div className={styles.userMenu}>
                <span className={styles.userName}>{user?.email}</span>
                <Link to={dashboardLink} className={styles.profileLink}>
                  <User size={20} />
                </Link>
                <button onClick={handleLogout} className={styles.logoutButton}>
                  <LogOut size={20} />
                </button>
              </div>
            </>
          ) : (
            <div className={styles.authLinks}>
              <Link to="/login" className={styles.link}>
                Login
              </Link>
              <Link to="/register" className={styles.link}>
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
