import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, MessageSquare, Heart, Bell, Plus, Upload } from 'lucide-react'
import MainLayout from '../../layouts/MainLayout'
import { CreateThreadModal } from '../../components/thread'
import { authService, threadService, notificationService } from '../../services'
import { wsManager } from '../../services/websocket'
import { useAuth } from '../../context/AuthContext'
import styles from './MemberDashboard.module.css'

export default function MemberDashboard() {
  const navigate = useNavigate()
  const { accessToken } = useAuth()
  const [profile, setProfile] = useState(null)
  const [myThreads, setMyThreads] = useState([])
  const [recentNotifications, setRecentNotifications] = useState([])
  const [stats, setStats] = useState({
    threadCount: 0,
    commentCount: 0,
    likeCount: 0
  })
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    bio: ''
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  useEffect(() => {
    setStats((prev) => ({
      ...prev,
      likeCount: myThreads.reduce((sum, thread) => sum + (thread.like_count || 0), 0),
      commentCount: myThreads.reduce((sum, thread) => sum + (thread.comment_count || 0), 0),
      threadCount: myThreads.length,
    }))
  }, [myThreads])

  useEffect(() => {
    if (!accessToken) {
      return
    }

    wsManager.connect(accessToken)

    const unsubscribeLike = wsManager.on('like', (payload) => {
      if (payload.entity_type !== 'thread' || !payload.entity_id) {
        return
      }
      setMyThreads((prev) =>
        prev.map((thread) =>
          thread.id === payload.entity_id
            ? { ...thread, like_count: payload.like_count ?? thread.like_count }
            : thread
        )
      )
    })

    const unsubscribeThread = wsManager.on('thread', (payload) => {
      if (payload.action === 'created') {
        const threadId = payload.thread?.id
        if (!threadId) {
          return
        }
        threadService.getThread(threadId)
          .then((response) => {
            const incoming = response.data
            if (incoming.author_id !== profile?.id) {
              return
            }
            setMyThreads((prev) => [incoming, ...prev.filter((t) => t.id !== incoming.id)])
          })
          .catch(() => {
            loadDashboardData()
          })
      } else if (payload.action === 'updated' && payload.thread?.id) {
        setMyThreads((prev) =>
          prev.map((thread) =>
            thread.id === payload.thread.id
              ? { ...thread, ...payload.thread }
              : thread
          )
        )
      } else if (payload.action === 'deleted' && payload.thread?.id) {
        setMyThreads((prev) => prev.filter((thread) => thread.id !== payload.thread.id))
      }
    })

    const unsubscribeNotification = wsManager.on('notification', (payload) => {
      setRecentNotifications((prev) => [payload, ...prev].slice(0, 5))
    })

    return () => {
      unsubscribeLike()
      unsubscribeThread()
      unsubscribeNotification()
    }
  }, [accessToken, profile?.id])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load profile
      const profileRes = await authService.me()
      setProfile(profileRes.data)
      setFormData({
        name: profileRes.data.name || '',
        bio: profileRes.data.bio || ''
      })

      // Load user's threads
      const threadsRes = await threadService.getThreads(1, 100)
      const threadPayload = threadsRes.data
      const threadItems = Array.isArray(threadPayload)
        ? threadPayload
        : (threadPayload.items || [])
      const ownThreads = threadItems.filter((thread) => thread.author_id === profileRes.data.id)
      setMyThreads(ownThreads)
      
      // Load recent notifications
      const notifRes = await notificationService.getNotifications(1, 5)
      setRecentNotifications(notifRes.data.items || [])

      setStats({
        threadCount: ownThreads.length,
        commentCount: ownThreads.reduce((sum, thread) => sum + (thread.comment_count || 0), 0),
        likeCount: ownThreads.reduce((sum, thread) => sum + (thread.like_count || 0), 0),
      })
    } catch (err) {
      console.error('Failed to load dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    setSaveError('')
    setSaveSuccess('')
    try {
      const response = await authService.updateProfile(formData)
      setProfile(response.data)
      setEditMode(false)
      setAvatarPreview('')
      setSaveSuccess('Profile updated successfully.')
    } catch (err) {
      setSaveError(err.response?.data?.detail || 'Failed to update profile.')
      console.error('Failed to update profile:', err)
    }
  }

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) {
      setAvatarPreview('')
      return
    }
    if (!file.type.startsWith('image/')) {
      setSaveError('Please upload an image file.')
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = String(reader.result || '')
      setAvatarPreview(dataUrl)
      setFormData((prev) => ({
        ...prev,
        avatar_url: dataUrl,
      }))
    }
    reader.onerror = () => {
      setSaveError('Failed to read selected image.')
    }
    reader.readAsDataURL(file)
  }

  const handleThreadCreated = () => {
    setShowCreateModal(false)
    loadDashboardData()
  }

  if (loading) {
    return (
      <MainLayout>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Loading dashboard...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>Member Dashboard</h1>
          <button
            className={styles.createButton}
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={20} />
            New Thread
          </button>
        </div>

        <div className={styles.grid}>
          {/* Profile Card */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h2>Profile</h2>
              <button
                className={styles.editButton}
                onClick={() => setEditMode(!editMode)}
              >
                {editMode ? 'Cancel' : 'Edit'}
              </button>
            </div>

            {editMode ? (
              <form onSubmit={handleUpdateProfile} className={styles.form}>
                {saveError && <div className={styles.error}>{saveError}</div>}
                {saveSuccess && <div className={styles.success}>{saveSuccess}</div>}
                <div className={styles.avatarSection}>
                  <div className={styles.avatarPreview}>
                    {avatarPreview || profile?.avatar_url ? (
                      <img 
                        src={avatarPreview || profile?.avatar_url} 
                        alt="Avatar" 
                        className={styles.avatar}
                      />
                    ) : (
                      <div className={styles.avatarPlaceholder}>
                        <User size={48} />
                      </div>
                    )}
                  </div>
                  <label htmlFor="avatar-upload" className={styles.uploadButton}>
                    <Upload size={16} />
                    Upload Avatar
                    <input
                      id="avatar-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className={styles.fileInput}
                    />
                  </label>
                </div>
                <div className={styles.formGroup}>
                  <label>Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Your name"
                  />
                </div>
                <div className={styles.formGroup}>
                  <label>Bio</label>
                  <textarea
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    placeholder="Tell us about yourself"
                    rows={4}
                  />
                </div>
                <button type="submit" className={styles.saveButton}>
                  Save Changes
                </button>
              </form>
            ) : (
              <div className={styles.profileInfo}>
                {saveSuccess && <div className={styles.success}>{saveSuccess}</div>}
                <div className={styles.infoRow}>
                  <User size={18} />
                  <div>
                    <span className={styles.label}>Email</span>
                    <span className={styles.value}>{profile?.email}</span>
                  </div>
                </div>
                {profile?.name && (
                  <div className={styles.infoRow}>
                    <User size={18} />
                    <div>
                      <span className={styles.label}>Name</span>
                      <span className={styles.value}>{profile.name}</span>
                    </div>
                  </div>
                )}
                {profile?.bio && (
                  <div className={styles.infoRow}>
                    <MessageSquare size={18} />
                    <div>
                      <span className={styles.label}>Bio</span>
                      <span className={styles.value}>{profile.bio}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Stats Cards */}
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <div className={styles.statIcon}>
                <MessageSquare size={24} />
              </div>
              <div className={styles.statContent}>
                <span className={styles.statValue}>{stats.threadCount}</span>
                <span className={styles.statLabel}>Threads</span>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statIcon}>
                <Heart size={24} />
              </div>
              <div className={styles.statContent}>
                <span className={styles.statValue}>{stats.likeCount}</span>
                <span className={styles.statLabel}>Likes</span>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statIcon}>
                <Bell size={24} />
              </div>
              <div className={styles.statContent}>
                <span className={styles.statValue}>{recentNotifications.length}</span>
                <span className={styles.statLabel}>Notifications</span>
              </div>
            </div>
          </div>

          {/* Recent Threads */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h2>My Recent Threads</h2>
              <button
                className={styles.viewAllButton}
                onClick={() => navigate('/threads')}
              >
                View All
              </button>
            </div>
            {myThreads.length > 0 ? (
              <div className={styles.threadsList}>
                {myThreads.slice(0, 5).map(thread => (
                  <div
                    key={thread.id}
                    className={styles.threadItem}
                    onClick={() => navigate(`/threads/${thread.id}`)}
                  >
                    <h3>{thread.title}</h3>
                    <div className={styles.threadMeta}>
                      <span>
                        <MessageSquare size={14} />
                        {thread.comment_count || 0}
                      </span>
                      <span>
                        <Heart size={14} />
                        {thread.like_count || 0}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.empty}>
                <p>You have not created any threads yet.</p>
                <button
                  className={styles.createButton}
                  onClick={() => setShowCreateModal(true)}
                >
                  <Plus size={18} />
                  Create Your First Thread
                </button>
              </div>
            )}
          </div>

          {/* Recent Notifications */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h2>Recent Notifications</h2>
            </div>
            {recentNotifications.length > 0 ? (
              <div className={styles.notificationsList}>
                {recentNotifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`${styles.notificationItem} ${
                      !notification.is_read ? styles.unread : ''
                    }`}
                  >
                    <p className={styles.notificationTitle}>{notification.title}</p>
                    <p className={styles.notificationMessage}>{notification.message}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.empty}>
                <p>No notifications yet.</p>
              </div>
            )}
          </div>
        </div>

        {showCreateModal && (
          <CreateThreadModal
            onClose={() => setShowCreateModal(false)}
            onThreadCreated={handleThreadCreated}
          />
        )}
      </div>
    </MainLayout>
  )
}
