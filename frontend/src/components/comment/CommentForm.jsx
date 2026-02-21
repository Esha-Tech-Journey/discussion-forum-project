import { useEffect, useMemo, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { commentService } from '../../services'
import { userService } from '../../services'
import styles from './CommentForm.module.css'

export default function CommentForm({
  threadId,
  parentId = null,
  onCommentCreated,
  onCancel,
  compact = false
}) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const textareaRef = useRef(null)
  const [mentionOpen, setMentionOpen] = useState(false)
  const [mentionQuery, setMentionQuery] = useState('')
  const [mentionStart, setMentionStart] = useState(null) // index of '@'
  const [mentionEnd, setMentionEnd] = useState(null) // current caret index
  const [suggestions, setSuggestions] = useState([])
  const [suggestionLoading, setSuggestionLoading] = useState(false)

  const resolveMentionContext = (nextContent, caretIndex) => {
    const idx = typeof caretIndex === 'number' ? caretIndex : nextContent.length
    const before = nextContent.slice(0, idx)

    const at = before.lastIndexOf('@')
    if (at < 0) {
      return { open: false, query: '', start: null, end: null }
    }

    const charBefore = at === 0 ? '' : before[at - 1]
    // Only trigger if @ is at start or preceded by whitespace.
    if (charBefore && !/\s/.test(charBefore)) {
      return { open: false, query: '', start: null, end: null }
    }

    const afterAt = before.slice(at + 1)
    // If user typed a space/newline after @username, mention is complete.
    if (/\s/.test(afterAt)) {
      return { open: false, query: '', start: null, end: null }
    }
    // Only allow "word" chars for mention query (matches backend parser).
    if (!/^\w*$/.test(afterAt)) {
      return { open: false, query: '', start: null, end: null }
    }

    return { open: true, query: afterAt, start: at, end: idx }
  }

  const handleContentChange = (e) => {
    const next = e.target.value
    const caret = e.target.selectionStart
    setContent(next)

    const ctx = resolveMentionContext(next, caret)
    setMentionOpen(ctx.open)
    setMentionQuery(ctx.query)
    setMentionStart(ctx.start)
    setMentionEnd(ctx.end)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && mentionOpen) {
      e.preventDefault()
      setMentionOpen(false)
      setMentionQuery('')
      setMentionStart(null)
      setMentionEnd(null)
      setSuggestions([])
    }
  }

  useEffect(() => {
    if (!mentionOpen) {
      setSuggestions([])
      setSuggestionLoading(false)
      return
    }

    let cancelled = false
    const handle = setTimeout(async () => {
      try {
        setSuggestionLoading(true)
        const res = await userService.suggestUsers(mentionQuery, 8)
        const items = Array.isArray(res.data) ? res.data : []
        if (!cancelled) {
          setSuggestions(items)
        }
      } catch (e) {
        if (!cancelled) {
          setSuggestions([])
        }
      } finally {
        if (!cancelled) {
          setSuggestionLoading(false)
        }
      }
    }, 200)

    return () => {
      cancelled = true
      clearTimeout(handle)
    }
  }, [mentionOpen, mentionQuery])

  const visibleSuggestions = useMemo(() => {
    if (!mentionOpen) return []
    return suggestions.filter((u) => (u?.name || '').trim().length > 0)
  }, [mentionOpen, suggestions])

  const applySuggestion = (user) => {
    const name = (user?.name || '').trim()
    if (!name || mentionStart === null || mentionEnd === null) {
      return
    }

    const before = content.slice(0, mentionStart)
    const after = content.slice(mentionEnd)
    const next = `${before}@${name} ${after}`
    setContent(next)
    setMentionOpen(false)
    setMentionQuery('')
    setMentionStart(null)
    setMentionEnd(null)
    setSuggestions([])

    // Restore caret right after inserted mention + space.
    const caret = (before + `@${name} `).length
    setTimeout(() => {
      if (!textareaRef.current) return
      textareaRef.current.focus()
      textareaRef.current.setSelectionRange(caret, caret)
    }, 0)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!content.trim()) {
      setError('Comment cannot be empty')
      return
    }

    setLoading(true)

    try {
      const response = await commentService.createComment({
        thread_id: threadId,
        content: content.trim(),
        parent_comment_id: parentId || undefined,
      })

      setContent('')
      onCommentCreated(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create comment')
      console.error('Create comment error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`${styles.form} ${compact ? styles.compact : ''}`}
    >
      {error && <div className={styles.error}>{error}</div>}

      <textarea
        value={content}
        onChange={handleContentChange}
        onKeyDown={handleKeyDown}
        placeholder={parentId ? 'Write a reply...' : 'Write a comment...'}
        disabled={loading}
        rows={compact ? 3 : 4}
        className={styles.textarea}
        ref={textareaRef}
      />

      {mentionOpen && (
        <div className={styles.mentionDropdown}>
          <div className={styles.mentionHeader}>
            <span>Mention</span>
            {suggestionLoading && <span className={styles.mentionLoading}>Searching...</span>}
          </div>
          {visibleSuggestions.length > 0 ? (
            <div className={styles.mentionList}>
              {visibleSuggestions.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  className={styles.mentionItem}
                  onClick={() => applySuggestion(u)}
                >
                  {u.avatar_url ? (
                    <img src={u.avatar_url} alt={u.name} className={styles.mentionAvatar} />
                  ) : (
                    <div className={styles.mentionAvatarFallback}>
                      {(u.name || '?').charAt(0).toUpperCase()}
                    </div>
                  )}
                  <span className={styles.mentionName}>@{u.name}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className={styles.mentionEmpty}>
              {mentionQuery ? 'No matches' : 'Type a name to search'}
            </div>
          )}
        </div>
      )}

      <div className={styles.actions}>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className={styles.cancelButton}
            disabled={loading}
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className={styles.submitButton}
          disabled={loading || !content.trim()}
        >
          <Send size={16} />
          {loading ? 'Posting...' : parentId ? 'Reply' : 'Comment'}
        </button>
      </div>
    </form>
  )
}
