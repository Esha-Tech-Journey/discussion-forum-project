import { memo } from 'react'
import Comment from './Comment'
import styles from './CommentTree.module.css'

// Build nested comment tree from flat list
function buildCommentTree(comments) {
  const commentMap = new Map()
  const roots = []

  // Create map of all comments
  comments.forEach(comment => {
    commentMap.set(comment.id, { ...comment, children: [] })
  })

  // Build tree structure
  comments.forEach(comment => {
    const node = commentMap.get(comment.id)
    const parentId = comment.parent_comment_id ?? comment.parent_id
    if (parentId) {
      const parent = commentMap.get(parentId)
      if (parent) {
        parent.children.push(node)
      } else {
        roots.push(node)
      }
    } else {
      roots.push(node)
    }
  })

  return roots
}

const CommentTree = memo(({
  comments,
  threadId,
  currentUserId = null,
  canModerate = false,
  onDeleteComment = null,
}) => {
  const commentTree = buildCommentTree(comments)

  if (commentTree.length === 0) {
    return null
  }

  return (
    <div className={styles.tree}>
      {commentTree.map(comment => (
        <Comment
          key={comment.id}
          comment={comment}
          threadId={threadId}
          depth={0}
          currentUserId={currentUserId}
          canModerate={canModerate}
          onDeleteComment={onDeleteComment}
        />
      ))}
    </div>
  )
})

CommentTree.displayName = 'CommentTree'

export default CommentTree
