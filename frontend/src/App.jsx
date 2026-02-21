import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThreadsProvider } from './context/ThreadsContext'
import { NotificationsProvider } from './context/NotificationsContext'
import { ProtectedRoute, RoleRoute, PublicRoute } from './routes/RouteGuards'

// Pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import ThreadsPage from './pages/thread/ThreadsPage'
import ThreadDetailPage from './pages/thread/ThreadDetailPage'
import SearchPage from './pages/SearchPage'
import MemberDashboard from './pages/dashboard/MemberDashboard'
import ModeratorDashboard from './pages/dashboard/ModeratorDashboard'
import AdminDashboard from './pages/dashboard/AdminDashboard'
import AdminUserProfile from './pages/dashboard/AdminUserProfile'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <AuthProvider>
        <ThreadsProvider>
          <NotificationsProvider>
            <Routes>
              {/* Auth Routes */}
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <LoginPage />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <RegisterPage />
                  </PublicRoute>
                }
              />
              <Route
                path="/reset-password"
                element={
                  <PublicRoute>
                    <ResetPasswordPage />
                  </PublicRoute>
                }
              />

              {/* Public Routes */}
              <Route
                path="/threads"
                element={
                  <ProtectedRoute>
                    <ThreadsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/threads/:id"
                element={
                  <ProtectedRoute>
                    <ThreadDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/search"
                element={
                  <ProtectedRoute>
                    <SearchPage />
                  </ProtectedRoute>
                }
              />
              {/* Member Dashboard */}
              <Route
                path="/dashboard/member"
                element={
                  <ProtectedRoute>
                    <MemberDashboard />
                  </ProtectedRoute>
                }
              />

              {/* Moderator Dashboard */}
              <Route
                path="/dashboard/moderator"
                element={
                  <RoleRoute allowedRoles={['MODERATOR', 'ADMIN']}>
                    <ModeratorDashboard />
                  </RoleRoute>
                }
              />

              {/* Admin Dashboard */}
              <Route
                path="/dashboard/admin"
                element={
                  <RoleRoute allowedRoles={['ADMIN']}>
                    <AdminDashboard />
                  </RoleRoute>
                }
              />

              {/* Admin Routes */}
              <Route
                path="/admin/users"
                element={
                  <RoleRoute allowedRoles={['ADMIN']}>
                    <AdminDashboard section="users" />
                  </RoleRoute>
                }
              />
              <Route
                path="/admin/moderation"
                element={
                  <RoleRoute allowedRoles={['ADMIN']}>
                    <AdminDashboard section="moderation" />
                  </RoleRoute>
                }
              />
              <Route
                path="/admin/reviews"
                element={
                  <RoleRoute allowedRoles={['ADMIN']}>
                    <ModeratorDashboard adminView />
                  </RoleRoute>
                }
              />
              <Route
                path="/admin/user/:id"
                element={
                  <RoleRoute allowedRoles={['ADMIN']}>
                    <AdminUserProfile />
                  </RoleRoute>
                }
              />

              {/* Redirect root */}
              <Route path="/" element={<Navigate to="/threads" replace />} />

              {/* 404 */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </NotificationsProvider>
        </ThreadsProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
