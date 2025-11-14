import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession, ModelInfo, HardwareDevice } from '@src/types'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const isLoading = ref(false)
  const currentModel = ref<ModelInfo | null>(null)
  const currentHardware = ref<HardwareDevice | null>(null)
  const streamingMessage = ref<string>('')
  const isStreaming = ref(false)

  const currentSession = computed(() => 
    sessions.value.find(s => s.id === currentSessionId.value) || null
  )

  const currentMessages = computed(() => 
    currentSession.value?.messages || []
  )

  const createSession = (title: string = 'New Chat'): string => {
    const session: ChatSession = {
      id: `session_${Date.now()}`,
      title,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      model: currentModel.value,
      hardware: currentHardware.value
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    return session.id
  }

  const selectSession = (sessionId: string): void => {
    currentSessionId.value = sessionId
  }

  const deleteSession = (sessionId: string): void => {
    const index = sessions.value.findIndex(s => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = sessions.value[0]?.id || null
      }
    }
  }

  const addMessage = (message: ChatMessage): void => {
    const session = currentSession.value
    if (session) {
      session.messages.push(message)
      session.updatedAt = new Date()
    }
  }

  const updateLastMessage = (content: string): void => {
    const session = currentSession.value
    if (session && session.messages.length > 0) {
      const lastMessage = session.messages[session.messages.length - 1]
      if (lastMessage.role === 'assistant') {
        lastMessage.content = content
        session.updatedAt = new Date()
      }
    }
  }

  const setCurrentModel = (model: ModelInfo | null): void => {
    currentModel.value = model
    if (currentSession.value) {
      currentSession.value.model = model
    }
  }

  const setCurrentHardware = (hardware: HardwareDevice | null): void => {
    currentHardware.value = hardware
    if (currentSession.value) {
      currentSession.value.hardware = hardware
    }
  }

  const startStreaming = (): void => {
    isStreaming.value = true
    streamingMessage.value = ''
  }

  const updateStreamingMessage = (chunk: string): void => {
    streamingMessage.value += chunk
  }

  const stopStreaming = (): void => {
    isStreaming.value = false
    if (streamingMessage.value && currentSession.value) {
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: streamingMessage.value,
        timestamp: new Date(),
        model: currentModel.value?.name,
        hardware: currentHardware.value?.type
      }
      addMessage(assistantMessage)
      streamingMessage.value = ''
    }
  }

  const addUserMessage = (content: string): void => {
    if (!currentSessionId.value) {
      createSession(content.slice(0, 50))
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: new Date()
    }
    addMessage(userMessage)
  }

  const addErrorMessage = (error: string): void => {
    const errorMessage: ChatMessage = {
      id: `msg_${Date.now()}_error`,
      role: 'assistant',
      content: `Sorry, I encountered an error: ${error}`,
      timestamp: new Date(),
      isError: true
    }
    addMessage(errorMessage)
  }

  const setStreaming = (streaming: boolean): void => {
    isStreaming.value = streaming
    if (streaming) {
      streamingMessage.value = ''
    }
  }

  const appendStreamingMessage = (chunk: string): void => {
    streamingMessage.value += chunk
  }

  const completeStreamingMessage = (fullResponse: string): void => {
    if (currentSession.value) {
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date(),
        model: currentModel.value?.name,
        hardware: currentHardware.value?.type
      }
      addMessage(assistantMessage)
      streamingMessage.value = ''
    }
  }

  const simulateChatResponse = async (content: string): Promise<string> => {
    // Simulate streaming response
    const responses = [
      'I understand your question about ' + content.slice(0, 20) + '. ',
      'Based on my analysis, ',
      'the solution involves several key steps. ',
      'First, you need to ensure proper configuration. ',
      'Then, implement the recommended approach. ',
      'This should resolve your issue effectively.'
    ]

    for (const chunk of responses) {
      await new Promise(resolve => setTimeout(resolve, 200))
      updateStreamingMessage(chunk)
    }

    return streamingMessage.value
  }

  const clearCurrentSession = (): void => {
    const session = currentSession.value
    if (session) {
      session.messages = []
      session.updatedAt = new Date()
    }
  }

  const renameSession = (sessionId: string, newTitle: string): void => {
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      session.title = newTitle
      session.updatedAt = new Date()
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    currentMessages,
    isLoading,
    currentModel,
    currentHardware,
    streamingMessage,
    isStreaming,
    createSession,
    selectSession,
    deleteSession,
    addMessage,
    addUserMessage,
    addErrorMessage,
    updateLastMessage,
    setCurrentModel,
    setCurrentHardware,
    setStreaming,
    startStreaming,
    updateStreamingMessage,
    appendStreamingMessage,
    completeStreamingMessage,
    stopStreaming,
    sendMessage,
    clearCurrentSession,
    renameSession
  }
})