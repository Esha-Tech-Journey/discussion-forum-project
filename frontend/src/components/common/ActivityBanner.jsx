import { RefreshCw } from 'lucide-react'
import styles from './ActivityBanner.module.css'

export default function ActivityBanner({ message, onRefresh }) {
  return (
    <div className={styles.banner}>
      <span className={styles.message}>{message}</span>
      <button onClick={onRefresh} className={styles.button}>
        <RefreshCw size={16} />
        Refresh
      </button>
    </div>
  )
}
