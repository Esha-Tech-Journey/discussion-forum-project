import { createContext, useState, useContext, useCallback } from 'react'

const ThreadsContext = createContext(null)

export const ThreadsProvider = ({ children }) => {
  const [threads, setThreads] = useState([])
  const [currentThread, setCurrentThread] = useState(null)
  const [comments, setComments] = useState([])
  const [threadCache, setThreadCache] = useState({})
  const [newActivityBanner, setNewActivityBanner] = useState(false)

  const addThread = useCallback((thread) => {
    setThreads(prev => {
      const exists = prev.some(t => t.id === thread.id)
      if (exists) {
        return prev.map(t => (t.id === thread.id ? { ...t, ...thread } : t))
      }
      return [thread, ...prev]
    })
  }, [])

  const updateThread = useCallback((threadId, updates) => {
    setThreads(prev =>
      prev.map(t => t.id === threadId ? { ...t, ...updates } : t)
    )
  }, [])

  const deleteThread = useCallback((threadId) => {
    setThreads(prev => prev.filter(t => t.id !== threadId))
  }, [])

  const setThreadsList = useCallback((list) => {
    setThreads(list)
  }, [])

  const addComment = useCallback((comment) => {
    setComments(prev => [...prev, comment])
  }, [])

  const updateComment = useCallback((commentId, updates) => {
    setComments(prev =>
      prev.map(c => c.id === commentId ? { ...c, ...updates } : c)
    )
  }, [])

  const deleteComment = useCallback((commentId) => {
    setComments(prev =>
      prev.map(c =>
        c.id === commentId
          ? { ...c, is_deleted: true, content: null, author: null }
          : c
      )
    )
  }, [])

  const cacheThread = useCallback((threadId, data) => {
    setThreadCache(prev => ({ ...prev, [threadId]: data }))
  }, [])

  const getCachedThread = useCallback((threadId) => {
    return threadCache[threadId]
  }, [threadCache])

  const value = {
    threads,
    setThreadsList,
    addThread,
    updateThread,
    deleteThread,
    currentThread,
    setCurrentThread,
    comments,
    addComment,
    updateComment,
    deleteComment,
    cacheThread,
    getCachedThread,
    newActivityBanner,
    setNewActivityBanner,
  }

  return (
    <ThreadsContext.Provider value={value}>{children}</ThreadsContext.Provider>
  )
}

export const useThreads = () => {
  const context = useContext(ThreadsContext)
  if (!context) {
    throw new Error('useThreads must be used within ThreadsProvider')
  }
  return context
}
