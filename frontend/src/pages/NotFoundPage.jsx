import { Link } from 'react-router-dom'
import styles from './NotFoundPage.module.css'

export default function NotFoundPage() {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <h1>404</h1>
        <p>Page not found</p>
        <Link to="/threads" className={styles.link}>
          Go back to forums
        </Link>
      </div>
    </div>
  )
}
