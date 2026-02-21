import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authService, notificationService } from '../../services'
import styles from './LoginPage.module.css'

const getErrorMessage = (err, fallback = 'Login failed. Please try again.') => {
  const detail = err?.response?.data?.detail
  if (!detail) return fallback

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => item?.msg || item?.message || '')
      .filter(Boolean)
    return messages.length ? messages.join(', ') : fallback
  }

  if (typeof detail === 'object') {
    return detail.msg || detail.message || fallback
  }

  return fallback
}

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authService.login(email, password)
      const { access_token, refresh_token } = response.data

      // Store tokens first so authenticated calls (e.g. /auth/me) include Authorization header.
      login(access_token, refresh_token, null)

      const userResponse = await authService.me()
      const profile = userResponse.data
      login(access_token, refresh_token, profile)

      const roleNames = (profile.roles || []).map(
        (role) => role.role_name || role.name || role
      )
      const isAdmin = roleNames.includes('ADMIN')
      const isModerator = roleNames.includes('MODERATOR')

      if (isModerator && !isAdmin) {
        try {
          const notificationRes = await notificationService.getNotifications(1, 20)
          const promotion = (notificationRes.data?.items || []).find((item) => (
            item?.type === 'ROLE_PROMOTION'
            && !item?.is_read
            && String(item?.title || '').toLowerCase().includes('moderator')
          ))

          if (promotion) {
            alert('You are promoted as moderator. Please login as moderator.')
            await notificationService.markAsRead(promotion.id)
          }
        } catch (promotionErr) {
          console.error('Failed to process promotion notice:', promotionErr)
        }
      }

      if (isAdmin) {
        sessionStorage.setItem('welcome_admin', '1')
        navigate('/dashboard/admin', { replace: true })
      } else if (isModerator) {
        navigate('/dashboard/moderator', { replace: true })
      } else {
        navigate('/threads', { replace: true })
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.formCard}>
        <h1 className={styles.title}>Login</h1>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className={styles.forgotPassword}>
            <Link to="/reset-password">Reset password?</Link>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className={styles.link}>
          Don&apos;t have an account? <Link to="/register">Register here</Link>
        </p>
      </div>
    </div>
  )
}
