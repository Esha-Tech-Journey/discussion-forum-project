import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, MessageSquare, Clock, User, Trash2 } from 'lucide-react'
import MainLayout from '../../layouts/MainLayout'
import { CommentTree, CommentForm } from '../../components/comment'
import { LikeButton, ActivityBanner } from '../../components/common'
import { threadService, commentService } from '../../services'
import { useThreads } from '../../context/ThreadsContext'
import { useAuth } from '../../context/AuthContext'
import { wsManager } from '../../services/websocket'
import styles from './ThreadDetailPage.module.css'
import { parseServerDate } from '../../utils/datetime'

export default function ThreadDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { accessToken, user } = useAuth()
  const { setCurrentThread, addComment, updateComment, newActivityBanner, setNewActivityBanner } = useThreads()
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [thread, setThread] = useState(null)
  const [threadComments, setThreadComments] = useState([])

  useEffect(() => {
    loadThread()
    loadComments()
  }, [id])

  useEffect(() => {
    // Connect WebSocket and listen for comment events
    if (accessToken && id) {
      wsManager.connect(accessToken)
      
      const unsubscribeComment = wsManager.on('comment', (payload) => {
        if (payload.thread_id === parseInt(id)) {
          if (payload.action === 'created') {
            loadComments()
          } else if (payload.action === 'updated') {
            updateComment(payload.comment.id, payload.comment)
            loadComments()
          }
        }
      })

      const unsubscribeLike = wsManager.on('like', (payload) => {
        if (payload.entity_type === 'thread' && payload.entity_id === parseInt(id)) {
          setThread(prev => prev ? { ...prev, like_count: payload.like_count ?? prev.like_count } : null)
        }
        if (payload.entity_type === 'comment') {
          loadComments()
        }
      })

      const unsubscribeThread = wsManager.on('thread', (payload) => {
        if (!payload.thread?.id || payload.thread.id !== parseInt(id)) {
          return
        }

        if (payload.action === 'deleted') {
          alert('This thread was removed by moderation.')
          navigate('/threads', { replace: true })
        } else if (payload.action === 'updated') {
          loadThread()
        }
      })

      return () => {
        unsubscribeComment()
        unsubscribeLike()
        unsubscribeThread()
      }
    }
  }, [accessToken, id, navigate])

  const loadThread = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await threadService.getThread(id)
      setThread(response.data)
      setCurrentThread(response.data)
    } catch (err) {
      setError('Failed to load thread. It may have been deleted.')
      console.error('Load thread error:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadComments = async () => {
    try {
      const response = await commentService.getComments(id, 1, 100)
      // Backend returns list directly, not pagination object
      setThreadComments(Array.isArray(response.data) ? response.data : [])
    } catch (err) {
      console.error('Load comments error:', err)
    }
  }

  const handleRefresh = () => {
    setNewActivityBanner(false)
    loadThread()
    loadComments()
  }

  const handleCommentCreated = (newComment) => {
    addComment(newComment)
    loadComments()
  }

  const handleDeleteThread = async () => {
    if (!thread?.id) return
    if (!window.confirm('Delete this thread?')) return

    try {
      await threadService.deleteThread(thread.id)
      navigate('/threads')
    } catch (err) {
      console.error('Delete thread error:', err)
      alert(err.response?.data?.detail || 'Failed to delete thread')
    }
  }

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return

    try {
      await commentService.deleteComment(commentId)
      loadComments()
    } catch (err) {
      console.error('Delete comment error:', err)
      alert(err.response?.data?.detail || 'Failed to delete comment')
    }
  }

  const formatDate = (dateString) => {
    return parseServerDate(dateString).toLocaleString()
  }

  const getAuthorName = (author) => {
    if (author?.is_deleted) {
      return 'User deleted'
    }
    if (author) {
      return author.name || author.email || 'Anonymous'
    }
    if (thread?.author_id) {
      return `User #${thread.author_id}`
    }
    return 'Anonymous'
  }

  if (loading) {
    return (
      <MainLayout>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Loading thread...</p>
        </div>
      </MainLayout>
    )
  }

  if (error || !thread) {
    return (
      <MainLayout>
        <div className={styles.error}>
          <p>{error || 'Thread not found'}</p>
          <button onClick={() => navigate('/threads')} className={styles.backButton}>
            <ArrowLeft size={20} />
            Back to Threads
          </button>
        </div>
      </MainLayout>
    )
  }

  const roleNames = (user?.roles || []).map((role) => role.role_name || role.name)
  const canModerate = roleNames.includes('ADMIN') || roleNames.includes('MODERATOR')
  const canDeleteThread = Number(user?.id) === Number(thread.author_id) || canModerate

  return (
    <MainLayout>
      <div className={styles.container}>
        <button onClick={() => navigate('/threads')} className={styles.backButton}>
          <ArrowLeft size={20} />
          Back
        </button>

        {newActivityBanner && (
          <ActivityBanner
            message="New comments available"
            onRefresh={handleRefresh}
          />
        )}

        <div className={styles.thread}>
          <div className={styles.threadHeader}>
            <h1 className={styles.title}>{thread.title}</h1>
            {canDeleteThread && (
              <button
                type="button"
                className={styles.deleteButton}
                onClick={handleDeleteThread}
              >
                <Trash2 size={16} />
                Delete Thread
              </button>
            )}
            
            {thread.tags && thread.tags.length > 0 && (
              <div className={styles.tags}>
                {thread.tags.map((tag, index) => (
                  <span key={index} className={styles.tag}>
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {thread.description && (
            <div className={styles.description}>
              <p>{thread.description}</p>
            </div>
          )}

          <div className={styles.threadMeta}>
            <div className={styles.author}>
              {thread.author?.avatar_url ? (
                <img
                  src={thread.author.avatar_url}
                  alt={getAuthorName(thread.author)}
                  className={styles.authorAvatar}
                />
              ) : (
                <User size={16} />
              )}
              <span>{getAuthorName(thread.author)}</span>
              <Clock size={14} />
              <span className={styles.date}>{formatDate(thread.created_at)}</span>
            </div>

            <div className={styles.stats}>
              <LikeButton
                entityType="thread"
                entityId={thread.id}
                initialLiked={thread.user_has_liked}
                initialCount={thread.like_count || 0}
              />
              <div className={styles.stat}>
                <MessageSquare size={18} />
                <span>{threadComments.length} comments</span>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.commentsSection}>
          <h2 className={styles.commentsTitle}>Comments</h2>
          
          <CommentForm
            threadId={thread.id}
            onCommentCreated={handleCommentCreated}
          />

          {threadComments.length > 0 ? (
            <CommentTree
              comments={threadComments}
              threadId={thread.id}
              currentUserId={Number(user?.id)}
              canModerate={canModerate}
              onDeleteComment={handleDeleteComment}
            />
          ) : (
            <div className={styles.noComments}>
              <p>No comments yet. Be the first to comment!</p>
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  )
}
