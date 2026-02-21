import { MessageSquare, Heart, Clock, User, Trash2 } from 'lucide-react'
import styles from './ThreadCard.module.css'
import { parseServerDate } from '../../utils/datetime'

export default function ThreadCard({
  thread,
  onClick,
  canDelete = false,
  onDelete = null,
}) {
  const formatDate = (dateString) => {
    const date = parseServerDate(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) {
      return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`
    } else if (diffHours < 24) {
      return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`
    } else if (diffDays < 7) {
      return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const getAuthorName = () => {
    if (thread.author?.is_deleted) {
      return 'User deleted'
    }
    if (thread.author) {
      return thread.author.name || thread.author.email || 'Anonymous'
    }
    if (thread.author_id) {
      return `User #${thread.author_id}`
    }
    return 'Anonymous'
  }

  return (
    <div className={styles.card} onClick={onClick}>
      <div className={styles.content}>
        <h3 className={styles.title}>{thread.title}</h3>
        {thread.description && (
          <p className={styles.description}>{thread.description}</p>
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

      <div className={styles.meta}>
        <div className={styles.author}>
          {thread.author?.avatar_url ? (
            <img
              src={thread.author.avatar_url}
              alt={getAuthorName()}
              className={styles.authorAvatar}
            />
          ) : (
            <User size={14} />
          )}
          <span>{getAuthorName()}</span>
        </div>
        <div className={styles.stats}>
          <div className={styles.stat}>
            <MessageSquare size={16} />
            <span>{thread.comment_count || 0}</span>
          </div>
          <div className={styles.stat}>
            <Heart size={16} />
            <span>{thread.like_count || 0}</span>
          </div>
          <div className={styles.stat}>
            <Clock size={14} />
            <span>{formatDate(thread.created_at)}</span>
          </div>
          {canDelete && onDelete && (
            <button
              type="button"
              className={styles.deleteButton}
              onClick={(e) => {
                e.stopPropagation()
                onDelete(thread.id)
              }}
            >
              <Trash2 size={14} />
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
