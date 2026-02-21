import { createContext, useState, useContext, useCallback, useEffect } from 'react'
import { authService } from '../services'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'))
  const [loading, setLoading] = useState(!!accessToken)

  const logout = useCallback(() => {
    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }, [])

  // Initialize session from stored token.
  useEffect(() => {
    const initSession = async () => {
      if (!accessToken) {
        setLoading(false)
        return
      }

      try {
        const response = await authService.me()
        setUser(response.data)
      } catch (err) {
        // Token points to deleted/invalid user: clear local session.
        logout()
      }
      setLoading(false)
    }

    initSession()
  }, [accessToken, logout])

  const login = useCallback((access_token, refresh_token, userData) => {
    setAccessToken(access_token)
    setRefreshToken(refresh_token)
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    setUser(userData)
  }, [])

  const refreshAccessToken = useCallback(async () => {
    if (!refreshToken) {
      logout()
      return false
    }
    // Will be called from API service on 401
    return true
  }, [refreshToken, logout])

  const value = {
    user,
    accessToken,
    refreshToken,
    loading,
    login,
    logout,
    refreshAccessToken,
    isAuthenticated: !!accessToken,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
