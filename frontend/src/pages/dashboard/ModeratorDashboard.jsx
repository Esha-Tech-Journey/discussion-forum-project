import { useState, useEffect, useCallback, useMemo } from 'react'
import { Shield, CheckCircle, Clock, XCircle, Edit3, Trash2, MessageSquare, Tag } from 'lucide-react'
import MainLayout from '../../layouts/MainLayout'
import AdminLayout from '../../layouts/AdminLayout'
import { Pagination } from '../../components/common'
import { moderationService, threadService, commentService } from '../../services'
import { wsManager } from '../../services/websocket'
import { useAuth } from '../../context/AuthContext'
import styles from './ModeratorDashboard.module.css'
import { renderTextWithMentions } from '../../utils/mentions.jsx'

const onlyThreadReviews = (items) =>
  (Array.isArray(items) ? items : []).filter((review) => review.content_type === 'THREAD')

const buildCommentTree = (comments) => {
  const byParent = new Map()
  comments.forEach((comment) => {
    const key = comment.parent_comment_id || 0
    if (!byParent.has(key)) {
      byParent.set(key, [])
    }
    byParent.get(key).push(comment)
  })

  const makeTree = (parentId = 0) => {
    const children = byParent.get(parentId) || []
    return children.map((comment) => ({
      ...comment,
      children: makeTree(comment.id),
    }))
  }

  return makeTree(0)
}

export default function ModeratorDashboard({ adminView = false }) {
  const Layout = adminView ? AdminLayout : MainLayout
  const { accessToken } = useAuth()
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('pending')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState({
    pending: 0,
    completed: 0,
    total: 0,
  })
  const [editingReviewId, setEditingReviewId] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [activeCommentsReviewId, setActiveCommentsReviewId] = useState(null)
  const [activeThreadTitle, setActiveThreadTitle] = useState('')
  const [threadComments, setThreadComments] = useState([])

  const loadStats = useCallback(async () => {
    try {
      const [pendingRes, completedRes] = await Promise.all([
        moderationService.getReviews(1, 100, 'pending'),
        moderationService.getReviews(1, 100, 'completed'),
      ])
      const pending = onlyThreadReviews(pendingRes.data)
      const completed = onlyThreadReviews(completedRes.data)
      setStats({
        pending: pending.length,
        completed: completed.length,
        total: pending.length + completed.length,
      })
    } catch (err) {
      console.error('Load stats error:', err)
    }
  }, [])

  const hydrateReviews = useCallback(async (reviewsList) => {
    const threadIds = [...new Set(
      reviewsList
        .map((review) => review.thread_id)
        .filter((id) => Number.isInteger(id))
    )]

    const threadMap = {}
    await Promise.all(threadIds.map(async (threadId) => {
      try {
        const response = await threadService.getThread(threadId)
        threadMap[threadId] = response.data
      } catch {
        threadMap[threadId] = null
      }
    }))

    return reviewsList.map((review) => ({
      ...review,
      thread: review.thread_id ? (threadMap[review.thread_id] || null) : null,
    }))
  }, [])

  const loadReviews = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      let rawReviews = []
      if (filter === 'all') {
        const [pendingRes, completedRes] = await Promise.all([
          moderationService.getReviews(page, 10, 'pending'),
          moderationService.getReviews(page, 10, 'completed'),
        ])
        const pending = onlyThreadReviews(pendingRes.data)
        const completed = onlyThreadReviews(completedRes.data)
        rawReviews = [...pending, ...completed]
      } else {
        const response = await moderationService.getReviews(page, 10, filter)
        rawReviews = onlyThreadReviews(response.data)
      }

      const hydrated = await hydrateReviews(rawReviews)
      const visible = hydrated.filter((review) => !!review.thread)
      setReviews(visible)
      setTotalPages(1)
      await loadStats()
    } catch (err) {
      setError('Failed to load moderation queue')
      console.error('Load reviews error:', err)
    } finally {
      setLoading(false)
    }
  }, [filter, hydrateReviews, loadStats, page])

  useEffect(() => {
    loadReviews()
  }, [loadReviews])

  useEffect(() => {
    if (!accessToken) {
      return
    }

    wsManager.connect(accessToken)
    const unsubscribe = wsManager.on('moderation_review', () => {
      loadReviews()
    })

    return () => {
      unsubscribe()
    }
  }, [accessToken, loadReviews])

  const handleTakeAction = async (reviewId, actionTaken) => {
    try {
      await moderationService.takeAction(
        reviewId,
        { status: 'COMPLETED', action_taken: actionTaken }
      )
      await loadReviews()
    } catch (err) {
      console.error('Action error:', err)
      alert('Failed to take action')
    }
  }

  const handleStartEditThread = (review) => {
    setEditingReviewId(review.id)
    setEditTitle(review.thread?.title || '')
    setEditDescription(review.thread?.description || '')
  }

  const handleSaveEditThread = async (review) => {
    if (!review.thread_id) return
    try {
      await threadService.updateThread(review.thread_id, {
        title: editTitle,
        description: editDescription,
      })
      await handleTakeAction(review.id, 'THREAD_EDITED')
      setEditingReviewId(null)
      setEditTitle('')
      setEditDescription('')
    } catch (err) {
      console.error('Edit thread error:', err)
      alert(err.response?.data?.detail || 'Failed to edit thread')
    }
  }

  const handleDeleteThread = async (review) => {
    if (!review.thread_id) return
    if (!window.confirm('Delete this thread?')) return

    try {
      await threadService.deleteThread(review.thread_id)
      await handleTakeAction(review.id, 'THREAD_DELETED')
    } catch (err) {
      console.error('Delete thread error:', err)
      alert(err.response?.data?.detail || 'Failed to delete thread')
    }
  }

  const loadThreadComments = async (threadId) => {
    try {
      const response = await commentService.getComments(threadId, 1, 200)
      const items = Array.isArray(response.data) ? response.data : []
      const visible = items.filter((item) => !item.is_deleted)
      setThreadComments(visible)
    } catch (err) {
      console.error('Load thread comments error:', err)
      alert('Failed to load thread comments')
    }
  }

  const openModerateComments = async (review) => {
    if (!review.thread_id) return
    setActiveCommentsReviewId(review.id)
    setActiveThreadTitle(review.thread?.title || `Thread #${review.thread_id}`)
    await loadThreadComments(review.thread_id)
  }

  const handleEditComment = async (comment) => {
    const next = window.prompt('Edit comment', comment.content || '')
    if (next === null) return
    const trimmed = next.trim()
    if (!trimmed) {
      alert('Comment cannot be empty')
      return
    }

    try {
      await commentService.updateComment(comment.id, { content: trimmed })
      const review = reviews.find((item) => item.id === activeCommentsReviewId)
      if (review) {
        await handleTakeAction(review.id, 'COMMENT_EDITED')
        await loadThreadComments(review.thread_id)
      }
    } catch (err) {
      console.error('Edit comment error:', err)
      alert(err.response?.data?.detail || 'Failed to edit comment')
    }
  }

  const handleDeleteComment = async (comment) => {
    if (!window.confirm('Delete this comment?')) return

    try {
      await commentService.deleteComment(comment.id)
      const review = reviews.find((item) => item.id === activeCommentsReviewId)
      if (review) {
        await handleTakeAction(review.id, 'COMMENT_DELETED')
        await loadThreadComments(review.thread_id)
      }
    } catch (err) {
      console.error('Delete comment error:', err)
      alert(err.response?.data?.detail || 'Failed to delete comment')
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const getStatusBadge = (status) => {
    const badges = {
      PENDING: { icon: Clock, color: 'var(--warning)', bg: 'rgba(245, 158, 11, 0.1)' },
      COMPLETED: { icon: CheckCircle, color: 'var(--success)', bg: 'rgba(16, 185, 129, 0.1)' },
    }

    const badge = badges[status] || badges.PENDING
    const Icon = badge.icon

    return (
      <span
        className={styles.badge}
        style={{ color: badge.color, backgroundColor: badge.bg }}
      >
        <Icon size={14} />
        {status}
      </span>
    )
  }

  const commentTree = useMemo(() => buildCommentTree(threadComments), [threadComments])

  const renderCommentNode = (comment, depth = 0) => {
    const authorName = comment.author?.name || comment.author?.email || 'User'
    return (
      <div key={comment.id} className={styles.commentNode} style={{ marginLeft: `${depth * 16}px` }}>
        <div className={styles.commentHead}>
          <strong>{authorName}</strong>
          <span>{formatDate(comment.created_at)}</span>
        </div>
        <p className={styles.commentBody}>
          {renderTextWithMentions(comment.content, styles.mention)}
        </p>
        <div className={styles.commentActions}>
          <button className={styles.smallBtn} onClick={() => handleEditComment(comment)}>
            Edit
          </button>
          <button className={`${styles.smallBtn} ${styles.dangerBtn}`} onClick={() => handleDeleteComment(comment)}>
            Delete
          </button>
        </div>
        {comment.children?.map((child) => renderCommentNode(child, depth + 1))}
      </div>
    )
  }

  return (
    <Layout>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1>Moderation Dashboard</h1>
            <p className={styles.subtitle}>Review and moderate flagged content</p>
          </div>
          <div className={styles.statsRow}>
            <div className={styles.statBadge}>
              <Clock size={18} />
              <span>{stats.pending} Pending</span>
            </div>
            <div className={styles.statBadge}>
              <CheckCircle size={18} />
              <span>{stats.completed} Completed</span>
            </div>
          </div>
        </div>

        <div className={styles.filters}>
          <button
            className={`${styles.filterButton} ${filter === 'pending' ? styles.active : ''}`}
            onClick={() => { setFilter('pending'); setPage(1); }}
          >
            Pending
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'completed' ? styles.active : ''}`}
            onClick={() => { setFilter('completed'); setPage(1); }}
          >
            Completed
          </button>
          <button
            className={`${styles.filterButton} ${filter === 'all' ? styles.active : ''}`}
            onClick={() => { setFilter('all'); setPage(1); }}
          >
            All
          </button>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={loadReviews} className={styles.retryButton}>
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading reviews...</p>
          </div>
        ) : reviews.length === 0 ? (
          <div className={styles.empty}>
            <Shield size={48} />
            <p>No reviews to display</p>
          </div>
        ) : (
          <>
            <div className={styles.reviewsList}>
              {reviews.map((review) => {
                const threadTitle = review.thread?.title || ''
                const tags = review.thread?.tags || []
                const canThreadAction = !!review.thread

                return (
                  <div key={review.id} className={styles.reviewCard}>
                    <div className={styles.reviewHeader}>
                      <div>
                        {getStatusBadge(review.status)}
                        <span className={styles.reviewType}>{review.content_type}</span>
                      </div>
                      <span className={styles.reviewDate}>{formatDate(review.created_at)}</span>
                    </div>

                    <div className={styles.reviewContent}>
                      <h3 className={styles.threadTitle}>{threadTitle}</h3>
                      <div className={styles.tagsRow}>
                        {tags.length > 0 ? tags.map((tag) => (
                          <span key={`${review.id}-${tag}`} className={styles.tagPill}>
                            <Tag size={12} /> {tag}
                          </span>
                        )) : <span className={styles.noTags}>No tags</span>}
                      </div>
                    </div>

                    {review.status === 'PENDING' && (
                      <div className={styles.actions}>
                        <button
                          className={`${styles.actionButton} ${styles.approve}`}
                          onClick={() => handleTakeAction(review.id, 'APPROVED')}
                        >
                          <CheckCircle size={16} />
                          Approve
                        </button>
                        <button
                          className={`${styles.actionButton} ${styles.remove}`}
                          onClick={() => handleTakeAction(review.id, 'DECLINED')}
                        >
                          <XCircle size={16} />
                          Decline
                        </button>
                        <button
                          className={`${styles.actionButton} ${styles.purpleOutline}`}
                          onClick={() => handleStartEditThread(review)}
                          disabled={!canThreadAction}
                        >
                          <Edit3 size={16} />
                          Edit Thread
                        </button>
                        <button
                          className={`${styles.actionButton} ${styles.purpleOutline}`}
                          onClick={() => handleDeleteThread(review)}
                          disabled={!canThreadAction}
                        >
                          <Trash2 size={16} />
                          Delete Thread
                        </button>
                        <button
                          className={`${styles.actionButton} ${styles.purpleOutline}`}
                          onClick={() => openModerateComments(review)}
                          disabled={!canThreadAction}
                        >
                          <MessageSquare size={16} />
                          Moderate Comments
                        </button>
                      </div>
                    )}

                    {editingReviewId === review.id && (
                      <div className={styles.editPanel}>
                        <input
                          className={styles.editInput}
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          placeholder="Thread title"
                        />
                        <textarea
                          className={styles.editTextarea}
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          placeholder="Thread description"
                          rows={4}
                        />
                        <div className={styles.editActions}>
                          <button className={styles.smallBtn} onClick={() => handleSaveEditThread(review)}>
                            Save
                          </button>
                          <button
                            className={styles.smallBtn}
                            onClick={() => {
                              setEditingReviewId(null)
                              setEditTitle('')
                              setEditDescription('')
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}

                    {review.action_taken && (
                      <div className={styles.actionTaken}>
                        <p><strong>Action:</strong> {review.action_taken}</p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {totalPages > 1 && (
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            )}
          </>
        )}
      </div>

      {activeCommentsReviewId && (
        <div className={styles.modalOverlay} onClick={() => setActiveCommentsReviewId(null)}>
          <div className={styles.modalPanel} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>Moderate Comments</h2>
              <button className={styles.smallBtn} onClick={() => setActiveCommentsReviewId(null)}>
                Close
              </button>
            </div>
            <p className={styles.modalSubtitle}>{activeThreadTitle}</p>

            <div className={styles.commentsList}>
              {commentTree.length > 0 ? commentTree.map((comment) => renderCommentNode(comment)) : (
                <p className={styles.noComments}>No comments in this thread.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
