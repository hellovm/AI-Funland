// Hardware acceleration types
export interface HardwareDevice {
  id: string
  name: string
  type: HardwareType
  memory?: number // in GB
  utilization?: number // percentage
  temperature?: number // celsius
  supported: boolean
  selected: boolean
}

export enum HardwareType {
  CPU = 'cpu',
  INTEL_GPU = 'intel_gpu',
  INTEL_NPU = 'intel_npu',
  NVIDIA_GPU = 'nvidia_gpu',
  AMD_GPU = 'amd_gpu'
}

export interface AccelerationConfig {
  primaryDevice: HardwareDevice
  secondaryDevices?: HardwareDevice[]
  mode: AccelerationMode
}

export enum AccelerationMode {
  SINGLE = 'single',
  MULTI = 'multi',
  HYBRID = 'hybrid'
}

// Model types
export interface ModelInfo {
  id: string
  name: string
  description: string
  size: number // in GB
  format: ModelFormat
  quantization?: string
  contextLength: number
  tags: string[]
  downloadUrl: string
  sha256?: string
  downloaded: boolean
  path?: string
}

export enum ModelFormat {
  GGUF = 'gguf',
  GGML = 'ggml',
  ONNX = 'onnx',
  PYTORCH = 'pytorch',
  TENSORFLOW = 'tensorflow'
}

// Download types
export interface DownloadTask {
  id: string
  modelId: string
  modelName: string
  totalSize: number
  downloadedSize: number
  speed: number // bytes per second
  status: DownloadStatus
  progress: number // percentage
  eta?: number // estimated time remaining in seconds
  error?: string
  resumeSupported: boolean
  threads: number
}

export enum DownloadStatus {
  PENDING = 'pending',
  DOWNLOADING = 'downloading',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  VERIFYING = 'verifying'
}

// Chat and inference types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  model?: string
  hardware?: string
  tokens?: number
  processingTime?: number
  isError?: boolean
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  model?: ModelInfo
  hardware?: HardwareDevice
  createdAt: Date
  updatedAt: Date
}

export interface InferenceParams {
  temperature: number
  maxTokens: number
  topP: number
  topK: number
  repeatPenalty: number
  frequencyPenalty: number
  presencePenalty: number
  stopSequences?: string[]
}

// Performance monitoring
export interface PerformanceMetrics {
  tokensPerSecond: number
  memoryUsage: number // MB
  cpuUsage: number // percentage
  gpuUsage?: number // percentage
  latency: number // ms
  throughput: number // tokens per second
}

// System information
export interface SystemInfo {
  os: string
  arch: string
  cpu: string
  memory: number // total RAM in GB
  pythonVersion: string
  nodeVersion: string
  hardwareDevices: HardwareDevice[]
}

// Plugin system
export interface Plugin {
  id: string
  name: string
  version: string
  description: string
  author: string
  enabled: boolean
  type: PluginType
  config?: Record<string, any>
}

export enum PluginType {
  TEXT_TO_IMAGE = 'text_to_image',
  TEXT_TO_VIDEO = 'text_to_video',
  IMAGE_TO_VIDEO = 'image_to_video',
  FACE_SWAP = 'face_swap',
  CUSTOM = 'custom'
}

// API responses
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Modelscope integration
export interface ModelscopeModel {
  id: string
  name: string
  description: string
  downloads: number
  likes: number
  tags: string[]
  cardUrl: string
  downloadUrl: string
  size: string
  lastModified: string
}