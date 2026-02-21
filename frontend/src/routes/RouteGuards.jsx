import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

export const RoleRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!user) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  // Check if user has required role
  const userRoles = user?.roles || []
  const hasRequiredRole = allowedRoles.some(role =>
    userRoles.some(userRole =>
      typeof userRole === 'object'
        ? (userRole.role_name === role || userRole.name === role)
        : userRole === role
    )
  )

  if (!hasRequiredRole) {
    return <Navigate to="/threads" replace />
  }

  return children
}

export const PublicRoute = ({ children }) => {
  const { isAuthenticated, user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (isAuthenticated && user) {
    const roleNames = (user.roles || []).map(
      (role) => role.role_name || role.name || role
    )
    if (roleNames.includes('ADMIN')) {
      return <Navigate to="/dashboard/admin" replace />
    }
    if (roleNames.includes('MODERATOR')) {
      return <Navigate to="/dashboard/moderator" replace />
    }
    return <Navigate to="/threads" replace />
  }
  return children
}
