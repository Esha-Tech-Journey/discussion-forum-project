import { useState, useEffect, useCallback } from 'react'
import { Shield, Users, Activity, Search, Heart } from 'lucide-react'
import AdminLayout from '../../layouts/AdminLayout'
import { Pagination } from '../../components/common'
import { userService, moderationService, threadService } from '../../services'
import { wsManager } from '../../services/websocket'
import { useAuth } from '../../context/AuthContext'
import styles from './AdminDashboard.module.css'
import { useNavigate } from 'react-router-dom'

export default function AdminDashboard({ section = 'dashboard' }) {
  const { accessToken } = useAuth()
  const navigate = useNavigate()
  const isUsersSection = section === 'users'
  const isModeratorsSection = section === 'moderation'
  const isRoleSection = isUsersSection || isModeratorsSection

  const [users, setUsers] = useState([])
  const [roleUsers, setRoleUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeThreads: 0,
    pendingReviews: 0,
  })
  const [selectedUser, setSelectedUser] = useState(null)
  const [roleChangeModal, setRoleChangeModal] = useState(false)

  useEffect(() => {
    const showWelcome = sessionStorage.getItem('welcome_admin')
    if (showWelcome === '1') {
      alert('Welcome Admin')
      sessionStorage.removeItem('welcome_admin')
    }
  }, [])

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await userService.getUsers(page, 10, searchQuery)
      setUsers(response.data.items || [])
      setTotalPages(response.data.pages || 1)
    } catch (err) {
      setError('Failed to load users')
      console.error('Load users error:', err)
    } finally {
      setLoading(false)
    }
  }, [page, searchQuery])

  const loadRoleUsers = useCallback(async () => {
    const roleName = isUsersSection ? 'MEMBER' : 'MODERATOR'
    const panelLabel = isUsersSection ? 'members' : 'moderators'
    try {
      setLoading(true)
      setError(null)
      const response = await userService.getUsersByRoleStats(roleName, page, 10, searchQuery)
      setRoleUsers(response.data.items || [])
      setTotalPages(response.data.pages || 1)
    } catch (err) {
      setError(`Failed to load ${panelLabel}`)
      console.error('Load role users error:', err)
    } finally {
      setLoading(false)
    }
  }, [isUsersSection, page, searchQuery])

  const loadStats = useCallback(async () => {
    try {
      const [usersRes, threadsRes, reviewsRes] = await Promise.all([
        userService.getUsers(1, 1),
        threadService.getThreads(1, 1),
        moderationService.getReviews(1, 100, 'pending'),
      ])
      const pendingThreadReviews = (reviewsRes.data || []).filter(
        (review) => review?.content_type === 'THREAD'
      )
      setStats({
        totalUsers: usersRes.data.total || 0,
        activeThreads: threadsRes.data.total || 0,
        pendingReviews: pendingThreadReviews.length,
      })
    } catch (err) {
      console.error('Load stats error:', err)
    }
  }, [])

  useEffect(() => {
    if (isRoleSection) {
      loadRoleUsers()
      return
    }

    loadUsers()
    loadStats()
  }, [isRoleSection, loadRoleUsers, loadUsers, loadStats])

  useEffect(() => {
    if (!accessToken) {
      return
    }

    wsManager.connect(accessToken)

    if (isRoleSection) {
      const unsubscribeUser = wsManager.on('user', () => loadRoleUsers())
      const unsubscribeThread = wsManager.on('thread', () => loadRoleUsers())
      const unsubscribeLike = wsManager.on('like', (payload) => {
        if (payload.entity_type === 'thread') {
          loadRoleUsers()
        }
      })

      return () => {
        unsubscribeUser()
        unsubscribeThread()
        unsubscribeLike()
      }
    }

    const unsubscribeUser = wsManager.on('user', (payload) => {
      if (!payload.user) {
        return
      }

      if (payload.action === 'created') {
        if (!searchQuery && page === 1) {
          setUsers((prev) =>
            [payload.user, ...prev.filter((item) => item.id !== payload.user.id)].slice(0, 10)
          )
        } else {
          loadUsers()
        }

        setStats((prev) => ({
          ...prev,
          totalUsers: prev.totalUsers + 1,
        }))
        return
      }

      if (payload.action === 'updated') {
        setUsers((prev) =>
          prev.map((item) => (item.id === payload.user.id ? { ...item, ...payload.user } : item))
        )
      }
    })

    const unsubscribeThread = wsManager.on('thread', (payload) => {
      if (payload.action !== 'created') {
        return
      }
      setStats((prev) => ({
        ...prev,
        activeThreads: prev.activeThreads + 1,
      }))
    })

    const unsubscribeModeration = wsManager.on('moderation_review', () => {
      loadStats()
    })

    return () => {
      unsubscribeUser()
      unsubscribeThread()
      unsubscribeModeration()
    }
  }, [accessToken, isRoleSection, loadRoleUsers, loadStats, loadUsers, page, searchQuery])

  const handleRoleChange = async (userId, newRole) => {
    try {
      await userService.changeRole(userId, newRole)
      setRoleChangeModal(false)
      setSelectedUser(null)
      if (isRoleSection) {
        loadRoleUsers()
      } else {
        loadUsers()
      }
    } catch (err) {
      console.error('Role change error:', err)
      alert('Failed to change user role')
    }
  }

  const handleToggleActive = async (userId, currentStatus) => {
    try {
      await userService.updateUser(userId, { is_active: !currentStatus })
      if (isRoleSection) {
        loadRoleUsers()
      } else {
        loadUsers()
      }
    } catch (err) {
      console.error('Toggle active error:', err)
      alert('Failed to update user status')
    }
  }

  const getRoleBadge = (role) => {
    const colors = {
      ADMIN: { bg: 'rgba(239, 68, 68, 0.1)', color: 'var(--error)' },
      MODERATOR: { bg: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' },
      MEMBER: { bg: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent)' },
    }

    const style = colors[role] || colors.MEMBER
    return (
      <span className={styles.roleBadge} style={{ backgroundColor: style.bg, color: style.color }}>
        {role}
      </span>
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (isRoleSection) {
    const sectionTitle = isUsersSection ? 'Members' : 'Moderators'
    const sectionSubtitle = isUsersSection
      ? 'Member accounts with post performance details'
      : 'Moderator accounts with post performance details'
    const sectionPlaceholder = isUsersSection
      ? 'Search members by username or email...'
      : 'Search moderators by username or email...'
    const emptyLabel = isUsersSection ? 'No members found' : 'No moderators found'
    const loadingLabel = isUsersSection ? 'Loading members...' : 'Loading moderators...'

    return (
      <AdminLayout>
        <div className={styles.container}>
          <div className={styles.header}>
            <div>
              <h1>{sectionTitle}</h1>
              <p className={styles.subtitle}>{sectionSubtitle}</p>
            </div>
          </div>

          <div className={styles.searchBar}>
            <Search size={20} />
            <input
              type="text"
              placeholder={sectionPlaceholder}
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
            />
          </div>

          {error && (
            <div className={styles.error}>
              {error}
              <button onClick={loadRoleUsers} className={styles.retryButton}>
                Retry
              </button>
            </div>
          )}

          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <p>{loadingLabel}</p>
            </div>
          ) : roleUsers.length === 0 ? (
            <div className={styles.empty}>
              <Users size={48} />
              <p>{emptyLabel}</p>
            </div>
          ) : (
            <>
              <div className={styles.usersList}>
                {roleUsers.map((member) => (
                  <div key={member.id} className={styles.userCard}>
                    <div className={styles.userInfo}>
                      <div className={styles.userHeader}>
                        <button
                          type="button"
                          className={styles.userNameLink}
                          onClick={() => navigate(`/admin/user/${member.id}`)}
                        >
                          {member.name || member.email}
                        </button>
                        {getRoleBadge(member.roles?.[0]?.role_name || 'MEMBER')}
                        {!member.is_active && <span className={styles.inactiveBadge}>Inactive</span>}
                      </div>
                      <p className={styles.userEmail}>{member.email}</p>
                      <p className={styles.userDate}>Joined: {formatDate(member.created_at)}</p>
                    </div>

                    <div className={styles.memberMetrics}>
                      <div className={styles.memberMetricItem}>
                        <Activity size={16} />
                        <span>Threads</span>
                        <strong>{member.thread_count || 0}</strong>
                      </div>
                      <div className={styles.memberMetricItem}>
                        <Heart size={16} />
                        <span>Likes on Posts</span>
                        <strong>{member.received_like_count || 0}</strong>
                      </div>
                    </div>

                    <div className={styles.userActions}>
                      <button
                        className={styles.actionButton}
                        onClick={() => {
                          setSelectedUser(member)
                          setRoleChangeModal(true)
                        }}
                      >
                        Change Role
                      </button>
                      <button
                        className={`${styles.actionButton} ${!member.is_active ? styles.activate : styles.deactivate}`}
                        onClick={() => handleToggleActive(member.id, member.is_active)}
                      >
                        {member.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
              )}
            </>
          )}

          {roleChangeModal && selectedUser && (
            <div className={styles.modal} onClick={() => setRoleChangeModal(false)}>
              <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                <h2>Change Role for {selectedUser.name || selectedUser.email}</h2>
                <p>
                  Current role: <strong>{selectedUser.roles?.[0]?.role_name || 'MEMBER'}</strong>
                </p>

                <div className={styles.roleOptions}>
                  {['MEMBER', 'MODERATOR', 'ADMIN'].map((role) => (
                    <button
                      key={role}
                      className={`${styles.roleOption} ${(selectedUser.roles?.[0]?.role_name || 'MEMBER') === role ? styles.current : ''}`}
                      onClick={() => handleRoleChange(selectedUser.id, role)}
                      disabled={(selectedUser.roles?.[0]?.role_name || 'MEMBER') === role}
                    >
                      {getRoleBadge(role)}
                      <span className={styles.roleDescription}>
                        {role === 'ADMIN' && 'Full system access'}
                        {role === 'MODERATOR' && 'Can moderate content'}
                        {role === 'MEMBER' && 'Standard user access'}
                      </span>
                    </button>
                  ))}
                </div>

                <button
                  className={styles.cancelButton}
                  onClick={() => {
                    setRoleChangeModal(false)
                    setSelectedUser(null)
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1>Admin Dashboard</h1>
            <p className={styles.subtitle}>Manage users, roles, and system</p>
          </div>
        </div>

        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statIcon} style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}>
              <Users size={24} style={{ color: 'var(--accent)' }} />
            </div>
            <div>
              <p className={styles.statLabel}>Total Users</p>
              <p className={styles.statValue}>{stats.totalUsers}</p>
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statIcon} style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
              <Activity size={24} style={{ color: 'var(--success)' }} />
            </div>
            <div>
              <p className={styles.statLabel}>Active Threads</p>
              <p className={styles.statValue}>{stats.activeThreads}</p>
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statIcon} style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
              <Shield size={24} style={{ color: 'var(--warning)' }} />
            </div>
            <div>
              <p className={styles.statLabel}>Pending Reviews</p>
              <p className={styles.statValue}>{stats.pendingReviews}</p>
            </div>
          </div>
        </div>

        <div className={styles.searchBar}>
          <Search size={20} />
          <input
            type="text"
            placeholder="Search users by username or email..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setPage(1)
            }}
          />
        </div>

        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={loadUsers} className={styles.retryButton}>
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading users...</p>
          </div>
        ) : users.length === 0 ? (
          <div className={styles.empty}>
            <Users size={48} />
            <p>No users found</p>
          </div>
        ) : (
          <>
            <div className={styles.usersList}>
              {users.map((user) => (
                <div key={user.id} className={styles.userCard}>
                  <div className={styles.userInfo}>
                    <div className={styles.userHeader}>
                      <button
                        type="button"
                        className={styles.userNameLink}
                        onClick={() => navigate(`/admin/user/${user.id}`)}
                      >
                        {user.name || user.email}
                      </button>
                      {getRoleBadge(user.roles?.[0]?.role_name || 'MEMBER')}
                      {!user.is_active && <span className={styles.inactiveBadge}>Inactive</span>}
                    </div>
                    <p className={styles.userEmail}>{user.email}</p>
                    <p className={styles.userDate}>Joined: {formatDate(user.created_at)}</p>
                  </div>

                  <div className={styles.userActions}>
                    <button
                      className={styles.actionButton}
                      onClick={() => {
                        setSelectedUser(user)
                        setRoleChangeModal(true)
                      }}
                    >
                      Change Role
                    </button>
                    <button
                      className={`${styles.actionButton} ${!user.is_active ? styles.activate : styles.deactivate}`}
                      onClick={() => handleToggleActive(user.id, user.is_active)}
                    >
                      {user.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
            )}
          </>
        )}

        {roleChangeModal && selectedUser && (
          <div className={styles.modal} onClick={() => setRoleChangeModal(false)}>
            <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
              <h2>Change Role for {selectedUser.name || selectedUser.email}</h2>
              <p>
                Current role: <strong>{selectedUser.roles?.[0]?.role_name || 'MEMBER'}</strong>
              </p>

              <div className={styles.roleOptions}>
                {['MEMBER', 'MODERATOR', 'ADMIN'].map((role) => (
                  <button
                    key={role}
                    className={`${styles.roleOption} ${(selectedUser.roles?.[0]?.role_name || 'MEMBER') === role ? styles.current : ''}`}
                    onClick={() => handleRoleChange(selectedUser.id, role)}
                    disabled={(selectedUser.roles?.[0]?.role_name || 'MEMBER') === role}
                  >
                    {getRoleBadge(role)}
                    <span className={styles.roleDescription}>
                      {role === 'ADMIN' && 'Full system access'}
                      {role === 'MODERATOR' && 'Can moderate content'}
                      {role === 'MEMBER' && 'Standard user access'}
                    </span>
                  </button>
                ))}
              </div>

              <button
                className={styles.cancelButton}
                onClick={() => {
                  setRoleChangeModal(false)
                  setSelectedUser(null)
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
