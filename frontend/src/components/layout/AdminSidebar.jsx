import { Link, useLocation } from 'react-router-dom'
import { Home, Shield, Users, BarChart3, MessageSquare, X } from 'lucide-react'
import styles from './AdminSidebar.module.css'

export default function AdminSidebar({ isOpen, onClose }) {
  const location = useLocation()

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
            <h3 className={styles.sectionTitle}>Admin</h3>
            <Link
              to="/dashboard/admin"
              className={`${styles.navItem} ${isActive('/dashboard/admin') ? styles.active : ''}`}
              onClick={onClose}
            >
              <BarChart3 size={20} />
              <span>Dashboard</span>
            </Link>
            <Link
              to="/admin/users"
              className={`${styles.navItem} ${isActive('/admin/users') ? styles.active : ''}`}
              onClick={onClose}
            >
              <Users size={20} />
              <span>Users</span>
            </Link>
            <Link
              to="/admin/moderation"
              className={`${styles.navItem} ${isActive('/admin/moderation') ? styles.active : ''}`}
              onClick={onClose}
            >
              <Shield size={20} />
              <span>Moderators</span>
            </Link>
            <Link
              to="/admin/reviews"
              className={`${styles.navItem} ${isActive('/admin/reviews') ? styles.active : ''}`}
              onClick={onClose}
            >
              <MessageSquare size={20} />
              <span>Reviews</span>
            </Link>
          </div>

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Main</h3>
            <Link
              to="/threads"
              className={`${styles.navItem} ${isActive('/threads') ? styles.active : ''}`}
              onClick={onClose}
            >
              <Home size={20} />
              <span>View Forum</span>
            </Link>
          </div>
        </nav>
      </aside>
    </>
  )
}
