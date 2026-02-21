import { useEffect, useState, memo } from 'react'
import { ChevronDown, ChevronRight, MessageSquare, Trash2 } from 'lucide-react'
import CommentForm from './CommentForm'
import { LikeButton } from '../common'
import styles from './Comment.module.css'
import { parseServerDate } from '../../utils/datetime'
import { renderTextWithMentions } from '../../utils/mentions.jsx'

const Comment = memo(({
  comment,
  threadId,
  depth = 0,
  currentUserId = null,
  canModerate = false,
  onDeleteComment = null,
}) => {
  const [collapsed, setCollapsed] = useState(false)
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [replies, setReplies] = useState(comment.children || [])

  useEffect(() => {
    setReplies(comment.children || [])
  }, [comment.children])

  const maxDepth = 6 // Maximum nesting level before flattening
  const isDeep = depth >= maxDepth

  const handleReplyCreated = (newReply) => {
    setReplies([...replies, { ...newReply, children: [] }])
    setShowReplyForm(false)
    setCollapsed(false)
  }

  const getAuthorName = () => {
    if (comment.author?.is_deleted) {
      return 'User deleted'
    }
    if (comment.author) {
      return comment.author.name || comment.author.email || 'Anonymous'
    }
    if (comment.author_id) {
      return `User #${comment.author_id}`
    }
    return 'Anonymous'
  }

  const formatDate = (dateString) => {
    const date = parseServerDate(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  // Soft delete UX: Show placeholder for deleted comment but keep children
  if (comment.is_deleted) {
    return (
      <div className={styles.comment} style={{ marginLeft: `${depth * 20}px` }}>
        <div className={styles.deletedContent}>
          <span className={styles.deletedText}>[ Comment deleted ]</span>
        </div>
        
        {/* Show children even if parent is deleted */}
        {replies.length > 0 && !collapsed && (
          <div className={styles.children}>
            {replies.map(reply => (
              <Comment
                key={reply.id}
                comment={reply}
                threadId={threadId}
                depth={depth + 1}
                currentUserId={currentUserId}
                canModerate={canModerate}
                onDeleteComment={onDeleteComment}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const canDeleteComment =
    Number(currentUserId) === Number(comment.author_id) || canModerate

  return (
    <div className={styles.comment} style={{ marginLeft: isDeep ? 0 : `${depth * 20}px` }}>
      <div className={styles.content}>
        <div className={styles.header}>
          <div className={styles.author}>
            {comment.author?.avatar_url && (
              <img
                src={comment.author.avatar_url}
                alt={getAuthorName()}
                className={styles.authorAvatar}
              />
            )}
            <span className={styles.authorName}>{getAuthorName()}</span>
            <span className={styles.date}>{formatDate(comment.created_at)}</span>
          </div>

          {replies.length > 0 && (
            <button
              className={styles.collapseButton}
              onClick={() => setCollapsed(!collapsed)}
              aria-label={collapsed ? 'Expand replies' : 'Collapse replies'}
            >
              {collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
              <span>{replies.length}</span>
            </button>
          )}
        </div>

        <div className={styles.body}>
          <p>
            {renderTextWithMentions(comment.content, styles.mention)}
          </p>
        </div>

        <div className={styles.actions}>
          <LikeButton
            entityType="comment"
            entityId={comment.id}
            initialLiked={comment.user_has_liked}
            initialCount={comment.like_count || 0}
            compact
          />

          <button
            className={styles.actionButton}
            onClick={() => setShowReplyForm(!showReplyForm)}
          >
            <MessageSquare size={14} />
            Reply
          </button>

          {canDeleteComment && onDeleteComment && (
            <button
              className={`${styles.actionButton} ${styles.deleteButton}`}
              onClick={() => onDeleteComment(comment.id)}
            >
              <Trash2 size={14} />
              Delete
            </button>
          )}
        </div>

        {showReplyForm && (
          <div className={styles.replyForm}>
            <CommentForm
              threadId={threadId}
              parentId={comment.id}
              onCommentCreated={handleReplyCreated}
              onCancel={() => setShowReplyForm(false)}
              compact
            />
          </div>
        )}
      </div>

      {/* Recursive rendering of children */}
      {replies.length > 0 && !collapsed && (
        <div className={styles.children}>
          {replies.map(reply => (
            <Comment
              key={reply.id}
              comment={reply}
              threadId={threadId}
              depth={isDeep ? depth : depth + 1}
              currentUserId={currentUserId}
              canModerate={canModerate}
              onDeleteComment={onDeleteComment}
            />
          ))}
        </div>
      )}
    </div>
  )
})

Comment.displayName = 'Comment'

export default Comment
