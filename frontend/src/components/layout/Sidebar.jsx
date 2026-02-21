import { Link, useLocation } from 'react-router-dom'
import { Home, MessageSquare, Settings, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import styles from './Sidebar.module.css'

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth()
  const location = useLocation()
  const roleNames = (user?.roles || []).map(
    (role) => role.role_name || role.name || role
  )
  const isModerator = roleNames.includes('MODERATOR')
  const isAdmin = roleNames.includes('ADMIN')
  const dashboardPath = isAdmin
    ? '/dashboard/admin'
    : isModerator
      ? '/dashboard/moderator'
      : '/dashboard/member'

  const isActive = (path) => location.pathname === path

  return (
    <>
      {isOpen && <div className={styles.overlay} onClick={onClose} />}
      
      <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
        <button className={styles.closeButton} onClick={onClose}>
          <X size={24} />
        </button>

        <nav className={styles.nav}>
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Main</h3>
            <Link
              to="/threads"
              className={`${styles.navItem} ${isActive('/threads') ? styles.active : ''}`}
              onClick={onClose}
            >
              <Home size={20} />
              <span>Threads</span>
            </Link>
            <Link
              to={dashboardPath}
              className={`${styles.navItem} ${isActive('/dashboard/member') || isActive('/dashboard/moderator') || isActive('/dashboard/admin') ? styles.active : ''}`}
              onClick={onClose}
            >
              <MessageSquare size={20} />
              <span>Dashboard</span>
            </Link>
          </div>

          {isModerator && !isAdmin && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Moderation</h3>
              <Link
                to="/dashboard/moderator"
                className={`${styles.navItem} ${isActive('/dashboard/moderator') ? styles.active : ''}`}
                onClick={onClose}
              >
                <Settings size={20} />
                <span>Moderator Panel</span>
              </Link>
            </div>
          )}

          {isAdmin && (
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Admin</h3>
              <Link
                to="/dashboard/admin"
                className={`${styles.navItem} ${isActive('/dashboard/admin') ? styles.active : ''}`}
                onClick={onClose}
              >
                <Settings size={20} />
                <span>Admin Panel</span>
              </Link>
            </div>
          )}
        </nav>
      </aside>
    </>
  )
}
