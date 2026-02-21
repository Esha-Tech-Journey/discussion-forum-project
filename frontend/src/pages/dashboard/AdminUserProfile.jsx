import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Heart, Activity, Tag } from 'lucide-react'
import AdminLayout from '../../layouts/AdminLayout'
import { userService } from '../../services'
import styles from './AdminUserProfile.module.css'

const getPrimaryRole = (roles) => {
  const names = (roles || []).map((r) => r?.role_name || r?.name || r).filter(Boolean)
  return names[0] || 'MEMBER'
}

export default function AdminUserProfile() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await userService.getUserActivity(id, 10, 10, 10)
        setData(res.data)
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load user profile')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const user = data?.user
  const stats = data?.stats || {}
  const topTags = data?.top_tags || []
  const recentThreads = data?.recent_threads || []
  const recentComments = data?.recent_comments || []
  const recentLikes = data?.recent_likes || []

  const displayName = useMemo(() => {
    return (user?.name || '').trim() || user?.email || `User #${id}`
  }, [user?.name, user?.email, id])

  const role = getPrimaryRole(user?.roles)
  const avatarFallback = (displayName || 'U').charAt(0).toUpperCase()

  return (
    <AdminLayout>
      <div className={styles.container}>
        <button type="button" className={styles.backBtn} onClick={() => navigate(-1)}>
          <ArrowLeft size={18} />
          Back
        </button>

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading profile...</p>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <p>{error}</p>
          </div>
        ) : (
          <>
            <div className={styles.header}>
              <div className={styles.identity}>
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt={displayName} className={styles.avatar} />
                ) : (
                  <div className={styles.avatarFallback}>{avatarFallback}</div>
                )}
                <div className={styles.meta}>
                  <div className={styles.nameRow}>
                    <h1 className={styles.name}>{displayName}</h1>
                    <span className={styles.role}>{role}</span>
                    {user?.is_active === false && (
                      <span className={styles.inactive}>Inactive</span>
                    )}
                  </div>
                  <div className={styles.email}>{user?.email}</div>
                  {user?.bio && <div className={styles.bio}>{user.bio}</div>}
                </div>
              </div>

              <div className={styles.stats}>
                <div className={styles.statCard}>
                  <Activity size={18} />
                  <div>
                    <div className={styles.statValue}>{stats.threads ?? 0}</div>
                    <div className={styles.statLabel}>Threads</div>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <MessageSquare size={18} />
                  <div>
                    <div className={styles.statValue}>{stats.comments ?? 0}</div>
                    <div className={styles.statLabel}>Comments</div>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <Heart size={18} />
                  <div>
                    <div className={styles.statValue}>{stats.likes_given ?? 0}</div>
                    <div className={styles.statLabel}>Likes Given</div>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <Heart size={18} />
                  <div>
                    <div className={styles.statValue}>{stats.likes_received ?? 0}</div>
                    <div className={styles.statLabel}>Likes Received</div>
                  </div>
                </div>
              </div>
            </div>

            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Top Tags</h2>
              <div className={styles.tags}>
                {topTags.length > 0 ? topTags.map((t) => (
                  <span key={t.name} className={styles.tagPill}>
                    <Tag size={12} /> {t.name} <span className={styles.tagCount}>{t.count}</span>
                  </span>
                )) : (
                  <div className={styles.muted}>No tags yet.</div>
                )}
              </div>
            </div>

            <div className={styles.grid}>
              <div className={styles.panel}>
                <h2 className={styles.sectionTitle}>Recent Threads</h2>
                {recentThreads.length > 0 ? (
                  <div className={styles.list}>
                    {recentThreads.map((t) => (
                      <div key={t.id} className={styles.listItem}>
                        <Link to={`/threads/${t.id}`} className={styles.itemTitle}>
                          {t.title}
                        </Link>
                        <div className={styles.itemMeta}>
                          <span><Activity size={14} /> {t.comment_count ?? 0} comments</span>
                          <span><Heart size={14} /> {t.like_count ?? 0} likes</span>
                        </div>
                        <div className={styles.itemTags}>
                          {(t.tags || []).slice(0, 6).map((tag) => (
                            <span key={`${t.id}-${tag}`} className={styles.smallTag}>{tag}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={styles.muted}>No threads yet.</div>
                )}
              </div>

              <div className={styles.panel}>
                <h2 className={styles.sectionTitle}>Recent Comments</h2>
                {recentComments.length > 0 ? (
                  <div className={styles.list}>
                    {recentComments.map((c) => (
                      <div key={c.id} className={styles.listItem}>
                        <Link to={`/threads/${c.thread_id}`} className={styles.itemTitle}>
                          {c.thread_title || `Thread #${c.thread_id}`}
                        </Link>
                        <div className={styles.itemBody}>{c.content}</div>
                        <div className={styles.itemMeta}>
                          <span><Heart size={14} /> {c.like_count ?? 0} likes</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={styles.muted}>No comments yet.</div>
                )}
              </div>

              <div className={styles.panel}>
                <h2 className={styles.sectionTitle}>Recent Likes</h2>
                {recentLikes.length > 0 ? (
                  <div className={styles.list}>
                    {recentLikes.map((l) => (
                      <div key={l.id} className={styles.listItem}>
                        {l.target_type === 'thread' ? (
                          <>
                            <div className={styles.likeLabel}>Liked thread</div>
                            <Link to={`/threads/${l.thread_id}`} className={styles.itemTitle}>
                              {l.thread_title || `Thread #${l.thread_id}`}
                            </Link>
                          </>
                        ) : (
                          <>
                            <div className={styles.likeLabel}>Liked comment</div>
                            <Link to={`/threads/${l.thread_id}`} className={styles.itemTitle}>
                              {l.thread_title || `Thread #${l.thread_id}`}
                            </Link>
                            {l.comment_excerpt && (
                              <div className={styles.itemBody}>{l.comment_excerpt}</div>
                            )}
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={styles.muted}>No likes yet.</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  )
}

