<template>
  <div class="flex h-full bg-gray-50">
    <!-- Sidebar -->
    <div class="w-80 bg-white border-r border-gray-200 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-xl font-semibold text-gray-900">{{ $t('chat.title') }}</h1>
          <button
            @click="createNewSession"
            class="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            :title="$t('chat.newChat')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
          </button>
        </div>

        <!-- Model and Hardware Status -->
        <div class="space-y-2">
          <div v-if="currentModel" class="flex items-center text-sm text-gray-600">
            <span class="font-medium">{{ $t('chat.model') }}:</span>
            <span class="ml-1 truncate">{{ currentModel.name }}</span>
          </div>
          <div v-if="currentHardware" class="flex items-center text-sm text-gray-600">
            <span class="font-medium">{{ $t('chat.hardware') }}:</span>
            <span class="ml-1">{{ currentHardware.type }} ({{ currentHardware.utilization }}%)</span>
          </div>
        </div>
      </div>

      <!-- Chat Sessions -->
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="session in sessions"
          :key="session.id"
          @click="selectSession(session.id)"
          :class="[
            'p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors',
            currentSessionId === session.id ? 'bg-blue-50 border-blue-200' : ''
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-gray-900 truncate">
                {{ session.title }}
              </h3>
              <p class="text-xs text-gray-500 mt-1">
                {{ formatDate(session.updatedAt) }}
              </p>
            </div>
            <div class="flex items-center space-x-1 ml-2">
              <button
                @click.stop="renameSession(session.id)"
                class="p-1 text-gray-400 hover:text-gray-600 rounded"
                :title="$t('chat.rename')"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </button>
              <button
                @click.stop="deleteSession(session.id)"
                class="p-1 text-gray-400 hover:text-red-600 rounded"
                :title="$t('chat.delete')"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-if="sessions.length === 0" class="p-8 text-center text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
          <p>{{ $t('chat.noSessions') }}</p>
        </div>
      </div>
    </div>

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col">
      <!-- Chat Header -->
      <div class="bg-white border-b border-gray-200 p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h2 class="text-lg font-semibold text-gray-900">
              {{ currentSession?.title || $t('chat.selectSession') }}
            </h2>
            <div v-if="isStreaming || isLoading" class="flex items-center text-sm text-blue-600">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              {{ isStreaming ? $t('chat.thinking') : $t('chat.loading') }}
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="clearCurrentSession"
              class="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              :disabled="!currentSession || currentMessages.length === 0"
            >
              {{ $t('chat.clear') }}
            </button>
            <button
              @click="showSettings = true"
              class="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
              :title="$t('chat.settings')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
        <div v-if="!currentSession" class="flex items-center justify-center h-full text-gray-500">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
            <p class="text-lg">{{ $t('chat.welcome') }}</p>
            <p class="text-sm mt-2">{{ $t('chat.selectOrCreate') }}</p>
          </div>
        </div>

        <div v-else-if="currentMessages.length === 0" class="flex items-center justify-center h-full text-gray-500">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
            </svg>
            <p class="text-lg">{{ $t('chat.emptySession') }}</p>
            <p class="text-sm mt-2">{{ $t('chat.startConversation') }}</p>
          </div>
        </div>

        <div v-else>
          <div
            v-for="message in currentMessages"
            :key="message.id"
            :class="[
              'flex',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-3xl px-4 py-2 rounded-lg',
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.isError
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : 'bg-white text-gray-900 border border-gray-200'
              ]"
            >
              <div class="text-sm" v-html="formatMessage(message.content)"></div>
              <div class="flex items-center justify-between mt-2 text-xs opacity-70">
                <span>{{ formatTime(message.timestamp) }}</span>
                <div v-if="message.model || message.hardware" class="flex items-center space-x-2">
                  <span v-if="message.model">{{ message.model }}</span>
                  <span v-if="message.hardware">• {{ message.hardware }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Streaming Message -->
          <div v-if="isStreaming && streamingMessage" class="flex justify-start">
            <div class="max-w-3xl px-4 py-2 rounded-lg bg-white text-gray-900 border border-gray-200">
              <div class="text-sm" v-html="formatMessage(streamingMessage)"></div>
              <div class="flex items-center mt-2 text-xs text-gray-500">
                <div class="animate-pulse">{{ $t('chat.typing') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="bg-white border-t border-gray-200 p-4">
        <div class="flex items-end space-x-3">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="sendMessage"
            @keydown.enter.shift.prevent="inputMessage += '\\n'"
            :placeholder="$t('chat.inputPlaceholder')"
            :disabled="isLoading || !currentSession"
            class="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
            rows="1"
            style="max-height: 120px; min-height: 40px;"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || isLoading || !currentSession"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettings" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">{{ $t('chat.settings') }}</h3>
          <button
            @click="showSettings = false"
            class="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('chat.selectModel') }}</label>
            <select
              v-model="selectedModelId"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{{ $t('chat.noModelSelected') }}</option>
              <option v-for="model in availableModels" :key="model.id" :value="model.id">
                {{ model.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('chat.selectHardware') }}</label>
            <select
              v-model="selectedHardwareId"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{{ $t('chat.autoSelect') }}</option>
              <option v-for="hardware in availableHardware" :key="hardware.id" :value="hardware.id">
                {{ hardware.type }} - {{ hardware.name }} ({{ hardware.utilization }}%)
              </option>
            </select>
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button
            @click="showSettings = false"
            class="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            @click="applySettings"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {{ $t('common.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@stores/chat'
import { useModelsStore } from '@stores/models'
import { useHardwareStore } from '@stores/hardware'
import { useWebSocket } from '@services/websocket'
import type { ModelInfo, HardwareDevice } from '@src/types'

const { t } = useI18n()
const chatStore = useChatStore()
const modelsStore = useModelsStore()
const hardwareStore = useHardwareStore()

const inputMessage = ref('')
const showSettings = ref(false)
const selectedModelId = ref('')
const selectedHardwareId = ref('')
const messagesContainer = ref<HTMLElement>()

const {
  sessions,
  currentSessionId,
  currentSession,
  currentMessages,
  isLoading,
  currentModel,
  currentHardware,
  streamingMessage,
  isStreaming
} = chatStore

const availableModels = computed(() => modelsStore.models)
const availableHardware = computed(() => hardwareStore.hardware)

// WebSocket setup
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const clientId = ref(`vue-client-${Date.now()}`)
const { 
  wsService, 
  connectionState, 
  onMessage, 
  sendMessage, 
  sendChatMessage, 
  cancelStream,
  requestHardwareStatus,
  requestModelsList,
  isConnected 
} = useWebSocket(wsUrl, clientId.value)

const createNewSession = () => {
  chatStore.createSession()
}

// WebSocket message handlers
onMounted(() => {
  // Setup WebSocket message handlers
  onMessage('chat_stream_start', (message) => {
    console.log('Chat stream started:', message.stream_id)
    chatStore.setStreaming(true)
  })

  onMessage('chat_stream_chunk', (message) => {
    chatStore.appendStreamingMessage(message.chunk || '')
  })

  onMessage('chat_stream_complete', (message) => {
    chatStore.completeStreamingMessage(message.full_response || '')
    chatStore.setStreaming(false)
  })

  onMessage('chat_stream_error', (message) => {
    console.error('Chat stream error:', message.error)
    chatStore.addErrorMessage(message.error || 'Stream error occurred')
    chatStore.setStreaming(false)
  })

  onMessage('chat_stream_cancelled', (message) => {
    console.log('Chat stream cancelled:', message.stream_id)
    chatStore.setStreaming(false)
  })

  onMessage('hardware_status', (message) => {
    hardwareStore.updateHardwareStatus(message.hardware)
  })

  onMessage('models_list', (message) => {
    modelsStore.updateModelsList(message.models)
  })

  // Request initial data
  if (isConnected()) {
    requestHardwareStatus()
    requestModelsList()
  }
})

const selectSession = (sessionId: string) => {
  chatStore.selectSession(sessionId)
}

const deleteSession = (sessionId: string) => {
  if (confirm(t('chat.confirmDelete'))) {
    chatStore.deleteSession(sessionId)
  }
}

const renameSession = (sessionId: string) => {
  const session = sessions.find(s => s.id === sessionId)
  if (session) {
    const newTitle = prompt(t('chat.enterNewTitle'), session.title)
    if (newTitle && newTitle.trim()) {
      chatStore.renameSession(sessionId, newTitle.trim())
    }
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value || !currentSession.value || !isConnected()) return

  inputMessage.value = ''
  
  // Add user message to chat
  chatStore.addUserMessage(message)
  
  // Send message via WebSocket
  sendChatMessage(
    currentSession.value.id,
    message,
    currentModel.value?.id
  )
  
  scrollToBottom()
}

const clearCurrentSession = () => {
  if (confirm(t('chat.confirmClear'))) {
    chatStore.clearCurrentSession()
  }
}

const applySettings = () => {
  const model = availableModels.value.find(m => m.id === selectedModelId.value) || null
  const hardware = availableHardware.value.find(h => h.id === selectedHardwareId.value) || null
  
  chatStore.setCurrentModel(model)
  chatStore.setCurrentHardware(hardware)
  showSettings.value = false
}

const formatDate = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t('chat.justNow')
  if (minutes < 60) return t('chat.minutesAgo', { count: minutes })
  if (hours < 24) return t('chat.hoursAgo', { count: hours })
  if (days < 7) return t('chat.daysAgo', { count: days })
  
  return date.toLocaleDateString()
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString()
}

const formatMessage = (content: string) => {
  return content.replace(/\n/g, '<br>')
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

watch(currentMessages, () => {
  scrollToBottom()
}, { deep: true })

// Initialize with a default session if none exists
if (sessions.length === 0) {
  createNewSession()
}

// Set default selections in settings modal
selectedModelId.value = currentModel.value?.id || ''
selectedHardwareId.value = currentHardware.value?.id || ''
</script>