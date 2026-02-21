import { Header, AdminSidebar, Footer } from '../components/layout'
import styles from './AdminLayout.module.css'
import { useState } from 'react'

export default function AdminLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className={styles.container}>
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      <div className={styles.wrapper}>
        <AdminSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className={styles.content}>
          {children}
        </main>
      </div>

      <Footer />
    </div>
  )
}
