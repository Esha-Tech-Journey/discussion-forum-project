import { useState } from 'react'
import { Header, Sidebar, Footer } from '../components/layout'
import styles from './MainLayout.module.css'

export default function MainLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className={styles.container}>
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      <div className={styles.wrapper}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <main className={styles.content}>
          {children}
        </main>
      </div>

      <Footer />
    </div>
  )
}
