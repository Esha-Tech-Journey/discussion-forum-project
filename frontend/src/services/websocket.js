const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1'

class WebSocketManager {
  constructor() {
    this.ws = null
    this.token = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
    this.listeners = new Map()
    this.isIntentionallyClosed = false
  }

  connect(token) {
    // Prevent duplicate sockets when multiple components call connect during initial mount.
    if (
      this.ws
      && (
        this.ws.readyState === WebSocket.OPEN
        || this.ws.readyState === WebSocket.CONNECTING
      )
    ) {
      return
    }

    this.token = token
    this.isIntentionallyClosed = false

    try {
      this.ws = new WebSocket(`${WS_URL}/ws?token=${token}`)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.emit('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const eventType = data.type || data.event
          const payload = data.payload ?? data.data ?? {}

          if (eventType) {
            this.emit(eventType, payload)

            const normalized = this.normalizeEvent(eventType, payload)
            if (normalized) {
              this.emit(normalized.type, normalized.payload)
            }
          }

          this.emit('message', data)
        } catch (err) {
          console.error('Failed to parse WS message:', err)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.emit('disconnected')

        if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          setTimeout(() => this.connect(this.token), this.reconnectDelay)
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
    }
  }

  disconnect() {
    this.isIntentionallyClosed = true
    if (this.ws) {
      this.ws.close()
    }
    this.ws = null
  }

  send(type, payload = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }))
    }
  }

  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, [])
    }
    this.listeners.get(type).push(callback)

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(type)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  off(type, callback) {
    if (this.listeners.has(type)) {
      const callbacks = this.listeners.get(type)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  emit(type, payload) {
    if (this.listeners.has(type)) {
      this.listeners.get(type).forEach(callback => callback(payload))
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  normalizeEvent(eventType, payload) {
    switch (eventType) {
      case 'NEW_COMMENT':
        return {
          type: 'comment',
          payload: {
            action: 'created',
            comment_id: payload.comment_id,
            thread_id: payload.thread_id,
            content: payload.content,
            comment: payload.comment || null,
          },
        }
      case 'NEW_THREAD':
        return {
          type: 'thread',
          payload: {
            action: payload.action || 'created',
            thread: payload.thread || {
              id: payload.thread_id,
              title: payload.title,
            },
          },
        }
      case 'NEW_LIKE': {
        const entityType = payload.thread_id ? 'thread' : 'comment'
        const entityId = payload.thread_id || payload.comment_id
        return {
          type: 'like',
          payload: {
            action: payload.action || 'updated',
            entity_type: entityType,
            entity_id: entityId,
            like_count: payload.like_count,
          },
        }
      }
      case 'NEW_NOTIFICATION':
        return {
          type: 'notification',
          payload: {
            id: payload.notification_id,
            user_id: payload.user_id,
            actor_id: payload.actor_id,
            type: payload.type,
            title: payload.title,
            message: payload.message,
            entity_type: payload.entity_type,
            entity_id: payload.entity_id,
            is_read: payload.is_read,
            created_at: payload.created_at,
          },
        }
      case 'NEW_USER':
        return {
          type: 'user',
          payload: {
            action: payload.action || 'created',
            user: payload.user || null,
          },
        }
      case 'MODERATION_REVIEW':
        return {
          type: 'moderation_review',
          payload: {
            action: payload.action || 'created',
            review: payload.review || null,
          },
        }
      default:
        return null
    }
  }
}

export const wsManager = new WebSocketManager()
