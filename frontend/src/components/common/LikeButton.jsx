import { useEffect, useState } from 'react'
import { Heart } from 'lucide-react'
import { likeService } from '../../services'
import styles from './LikeButton.module.css'

export default function LikeButton({
  entityType,
  entityId,
  initialLiked = false,
  initialCount = 0,
  compact = false
}) {
  const [liked, setLiked] = useState(initialLiked)
  const [count, setCount] = useState(initialCount)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLiked(initialLiked)
  }, [initialLiked])

  useEffect(() => {
    setCount(initialCount)
  }, [initialCount])

  const handleToggleLike = async (e) => {
    e.stopPropagation()
    
    if (loading) return

    // Optimistic UI update
    const prevLiked = liked
    const prevCount = count
    
    setLiked(!liked)
    setCount(liked ? count - 1 : count + 1)
    setLoading(true)

    try {
      if (liked) {
        if (entityType === 'thread') {
          await likeService.unlikeThread(entityId)
        } else {
          await likeService.unlikeComment(entityId)
        }
      } else {
        if (entityType === 'thread') {
          await likeService.likeThread(entityId)
        } else {
          await likeService.likeComment(entityId)
        }
      }
    } catch (err) {
      // Rollback on error
      setLiked(prevLiked)
      setCount(prevCount)
      console.error('Like toggle error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggleLike}
      className={`${styles.button} ${liked ? styles.liked : ''} ${
        compact ? styles.compact : ''
      }`}
      disabled={loading}
      aria-label={liked ? 'Unlike' : 'Like'}
    >
      <Heart size={compact ? 14 : 18} fill={liked ? 'currentColor' : 'none'} />
      <span>{count}</span>
    </button>
  )
}
