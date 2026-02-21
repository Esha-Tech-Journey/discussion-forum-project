import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, RefreshCw } from 'lucide-react'
import MainLayout from '../../layouts/MainLayout'
import { ThreadCard, CreateThreadModal } from '../../components/thread'
import { Pagination, ActivityBanner } from '../../components/common'
import { threadService, searchService } from '../../services'
import { useThreads } from '../../context/ThreadsContext'
import { wsManager } from '../../services/websocket'
import { useAuth } from '../../context/AuthContext'
import styles from './ThreadsPage.module.css'

export default function ThreadsPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const query = (searchParams.get('q') || '').trim()
  const { accessToken, user } = useAuth()
  const {
    threads,
    setThreadsList,
    addThread,
    updateThread,
    deleteThread,
    newActivityBanner,
    setNewActivityBanner,
  } = useThreads()
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [totalPages, setTotalPages] = useState(1)
  const [totalThreads, setTotalThreads] = useState(0)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTags] = useState([])

  useEffect(() => {
    loadThreads()
  }, [page, selectedTags, query])

  useEffect(() => {
    // Connect WebSocket
    if (accessToken) {
      wsManager.connect(accessToken)
      
      // Listen for thread events
      const unsubscribeThread = wsManager.on('thread', (payload) => {
        if (payload.action === 'created') {
          const threadId = payload.thread?.id
          if (!threadId) {
            return
          }

          // Fetch the full thread and inject it immediately for live updates.
          threadService.getThread(threadId)
            .then((response) => {
              addThread(response.data)
              loadThreads()
            })
            .catch(() => {
              // Fallback to full reload if thread hydration fails.
              loadThreads()
            })
        } else if (payload.action === 'updated') {
          updateThread(payload.thread.id, payload.thread)
        } else if (payload.action === 'deleted' && payload.thread?.id) {
          deleteThread(payload.thread.id)
          setTotalThreads((prev) => Math.max(0, prev - 1))
        }
      })

      const unsubscribeLike = wsManager.on('like', (payload) => {
        if (payload.entity_type === 'thread' && payload.entity_id) {
          updateThread(payload.entity_id, {
            like_count: payload.like_count,
          })
        }
      })

      const unsubscribeComment = wsManager.on('comment', (payload) => {
        if (payload.action !== 'created' || !payload.thread_id) {
          return
        }

        threadService.getThread(payload.thread_id)
          .then((response) => {
            updateThread(payload.thread_id, {
              comment_count: response.data.comment_count,
            })
          })
          .catch(() => {
            // Fallback to full reload if thread fetch fails.
            loadThreads()
          })
      })

      return () => {
        unsubscribeThread()
        unsubscribeLike()
        unsubscribeComment()
      }
    }
  }, [accessToken, addThread, updateThread, deleteThread, page, pageSize, selectedTags])

  const loadThreads = async () => {
    try {
      setLoading(true)
      setError(null)
      if (query) {
        const response = await searchService.searchThreads(query, page, pageSize)
        const results = response.data?.results || []
        const total = response.data?.total ?? results.length
        const pages = Math.max(1, Math.ceil(total / pageSize))

        setThreadsList(results)
        setTotalPages(pages)
        setTotalThreads(total)
      } else {
        const response = await threadService.getThreads(
          page,
          pageSize,
          selectedTags.length > 0 ? selectedTags : null
        )
        const payload = response.data
        const items = Array.isArray(payload) ? payload : (payload.items || [])
        const total = Array.isArray(payload) ? items.length : (payload.total || items.length)
        const pages = Array.isArray(payload) ? 1 : (payload.pages || 1)

        setThreadsList(items)
        setTotalPages(pages)
        setTotalThreads(total)
      }
    } catch (err) {
      setError('Failed to load threads. Please try again.')
      console.error('Load threads error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    setNewActivityBanner(false)
    setPage(1)
    loadThreads()
  }

  const handleThreadCreated = (newThread) => {
    addThread(newThread)
    setShowCreateModal(false)
    setTotalThreads((prev) => prev + 1)
    if (page !== 1) {
      setPage(1)
    }
  }

  const handleThreadClick = (threadId) => {
    navigate(`/threads/${threadId}`)
  }

  const handleDeleteThread = async (threadId) => {
    if (!window.confirm('Delete this thread?')) return

    try {
      await threadService.deleteThread(threadId)
      deleteThread(threadId)
      setTotalThreads((prev) => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Delete thread error:', err)
      alert(err.response?.data?.detail || 'Failed to delete thread')
    }
  }

  const handlePageChange = (newPage) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <MainLayout>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Threads</h1>
            <p className={styles.subtitle}>
              {totalThreads} {totalThreads === 1 ? 'thread' : 'threads'}
            </p>
          </div>
          <button
            className={styles.createButton}
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={20} />
            New Thread
          </button>
        </div>

        {newActivityBanner && (
          <ActivityBanner
            message="New activity available"
            onRefresh={handleRefresh}
          />
        )}

        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={loadThreads} className={styles.retryButton}>
              <RefreshCw size={16} />
              Retry
            </button>
          </div>
        )}

        {loading && threads.length === 0 ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading threads...</p>
          </div>
        ) : threads.length === 0 ? (
          <div className={styles.empty}>
            <p>No threads yet. Be the first to create one!</p>
            <button
              className={styles.createButton}
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={20} />
              Create Thread
            </button>
          </div>
        ) : (
          <>
            <div className={styles.threadsList}>
              {threads.map((thread) => (
                <ThreadCard
                  key={thread.id}
                  thread={thread}
                  onClick={() => handleThreadClick(thread.id)}
                  canDelete={
                    Number(user?.id) === Number(thread.author_id) ||
                    (user?.roles || []).some((role) => ['ADMIN', 'MODERATOR'].includes(role.role_name || role.name))
                  }
                  onDelete={handleDeleteThread}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            )}
          </>
        )}

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
