/**
 * WebSocket service for real-time communication with backend
 * Handles chat streaming, hardware updates, and model management
 */

import { ref, reactive, onMounted, onUnmounted } from 'vue'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface ChatStreamEvent {
  type: 'chat_stream_start' | 'chat_stream_chunk' | 'chat_stream_complete' | 'chat_stream_error' | 'chat_stream_cancelled'
  stream_id: string
  session_id: string
  chunk?: string
  progress?: number
  error?: string
  full_response?: string
  timestamp: string
}

export interface HardwareStatusEvent {
  type: 'hardware_status'
  hardware: any
  timestamp: string
}

export interface ModelsListEvent {
  type: 'models_list'
  models: any[]
  timestamp: string
}

export interface WebSocketConnection {
  url: string
  protocols?: string[]
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnects?: number
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private clientId: string
  private reconnectAttempts = 0
  private maxReconnects = 5
  private reconnectInterval = 3000
  private messageHandlers: Map<string, (message: any) => void> = new Map()
  private connectionState = reactive({
    isConnected: false,
    isConnecting: false,
    error: null as string | null,
    reconnectAttempts: 0
  })

  constructor(url: string, clientId: string, options: Partial<WebSocketConnection> = {}) {
    this.url = url
    this.clientId = clientId
    this.maxReconnects = options.maxReconnects || 5
    this.reconnectInterval = options.reconnectInterval || 3000
    
    // Bind message handlers
    this.setupMessageHandlers()
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.connectionState.isConnected || this.connectionState.isConnecting) {
      return
    }

    this.connectionState.isConnecting = true
    this.connectionState.error = null

    try {
      const wsUrl = `${this.url}/ws/${this.clientId}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.connectionState.isConnected = true
        this.connectionState.isConnecting = false
        this.connectionState.reconnectAttempts = 0
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.connectionState.isConnected = false
        this.connectionState.isConnecting = false
        this.ws = null

        // Attempt reconnection if enabled
        if (this.reconnectAttempts < this.maxReconnects) {
          setTimeout(() => {
            this.reconnectAttempts++
            this.connectionState.reconnectAttempts = this.reconnectAttempts
            console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnects}`)
            this.connect()
          }, this.reconnectInterval)
        } else {
          this.connectionState.error = 'Max reconnection attempts reached'
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.connectionState.error = 'WebSocket connection error'
        this.connectionState.isConnecting = false
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.connectionState.error = 'Failed to create connection'
      this.connectionState.isConnecting = false
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connectionState.isConnected = false
    this.connectionState.isConnecting = false
  }

  /**
   * Send message to server
   */
  sendMessage(message: WebSocketMessage): void {
    if (!this.connectionState.isConnected || !this.ws) {
      console.warn('WebSocket not connected, message not sent:', message)
      return
    }

    try {
      this.ws.send(JSON.stringify(message))
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
    }
  }

  /**
   * Register message handler for specific message type
   */
  onMessage(type: string, handler: (message: any) => void): void {
    this.messageHandlers.set(type, handler)
  }

  /**
   * Remove message handler
   */
  offMessage(type: string): void {
    this.messageHandlers.delete(type)
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WebSocketMessage): void {
    const handler = this.messageHandlers.get(message.type)
    if (handler) {
      handler(message)
    } else {
      console.log('Unhandled message type:', message.type, message)
    }
  }

  /**
   * Setup default message handlers
   */
  private setupMessageHandlers(): void {
    // Connection established
    this.onMessage('connection_established', (message) => {
      console.log('Connection established with client ID:', message.client_id)
    })

    // Pong response
    this.onMessage('pong', (message) => {
      console.log('Pong received:', message.timestamp)
    })

    // Error messages
    this.onMessage('error', (message) => {
      console.error('Server error:', message.error)
      this.connectionState.error = message.error
    })
  }

  /**
   * Send ping message
   */
  ping(): void {
    this.sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Send chat message
   */
  sendChatMessage(sessionId: string, message: string, modelId?: string): void {
    this.sendMessage({
      type: 'chat_message',
      session_id: sessionId,
      message: message,
      model_id: modelId,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Cancel chat stream
   */
  cancelStream(streamId: string): void {
    this.sendMessage({
      type: 'cancel_stream',
      stream_id: streamId,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Request hardware status
   */
  requestHardwareStatus(): void {
    this.sendMessage({
      type: 'get_hardware_status',
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Request models list
   */
  requestModelsList(): void {
    this.sendMessage({
      type: 'get_models',
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Get connection state
   */
  getConnectionState() {
    return this.connectionState
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState.isConnected
  }
}

/**
 * Composable for using WebSocket service in Vue components
 */
export function useWebSocket(url: string, clientId: string, options: Partial<WebSocketConnection> = {}) {
  const wsService = new WebSocketService(url, clientId, options)
  const messageHandlers = ref<Map<string, (message: any) => void>>(new Map())

  // Setup additional message handlers
  const setupHandlers = () => {
    // Chat stream events
    wsService.onMessage('chat_stream_start', (message: ChatStreamEvent) => {
      const handler = messageHandlers.value.get('chat_stream_start')
      if (handler) handler(message)
    })

    wsService.onMessage('chat_stream_chunk', (message: ChatStreamEvent) => {
      const handler = messageHandlers.value.get('chat_stream_chunk')
      if (handler) handler(message)
    })

    wsService.onMessage('chat_stream_complete', (message: ChatStreamEvent) => {
      const handler = messageHandlers.value.get('chat_stream_complete')
      if (handler) handler(message)
    })

    wsService.onMessage('chat_stream_error', (message: ChatStreamEvent) => {
      const handler = messageHandlers.value.get('chat_stream_error')
      if (handler) handler(message)
    })

    wsService.onMessage('chat_stream_cancelled', (message: ChatStreamEvent) => {
      const handler = messageHandlers.value.get('chat_stream_cancelled')
      if (handler) handler(message)
    })

    // Hardware status
    wsService.onMessage('hardware_status', (message: HardwareStatusEvent) => {
      const handler = messageHandlers.value.get('hardware_status')
      if (handler) handler(message)
    })

    // Models list
    wsService.onMessage('models_list', (message: ModelsListEvent) => {
      const handler = messageHandlers.value.get('models_list')
      if (handler) handler(message)
    })
  }

  // Register message handler
  const onMessage = (type: string, handler: (message: any) => void) => {
    messageHandlers.value.set(type, handler)
  }

  // Connect on mount
  onMounted(async () => {
    setupHandlers()
    await wsService.connect()
  })

  // Disconnect on unmount
  onUnmounted(() => {
    wsService.disconnect()
  })

  return {
    wsService,
    connectionState: wsService.getConnectionState(),
    onMessage,
    sendMessage: wsService.sendMessage.bind(wsService),
    sendChatMessage: wsService.sendChatMessage.bind(wsService),
    cancelStream: wsService.cancelStream.bind(wsService),
    requestHardwareStatus: wsService.requestHardwareStatus.bind(wsService),
    requestModelsList: wsService.requestModelsList.bind(wsService),
    isConnected: wsService.isConnected.bind(wsService)
  }
}

export default WebSocketService