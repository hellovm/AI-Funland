import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { HardwareDevice, AccelerationConfig, HardwareType } from '@types/index'

export const useHardwareStore = defineStore('hardware', () => {
  const devices = ref<HardwareDevice[]>([])
  const selectedConfig = ref<AccelerationConfig>({
    primaryDevice: {
      id: 'cpu',
      name: 'CPU',
      type: HardwareType.CPU,
      supported: true,
      selected: true
    },
    mode: 'single'
  })
  const isDetecting = ref(false)

  const availableDevices = computed(() => devices.value.filter(d => d.supported))
  const selectedDevices = computed(() => {
    const selected = [selectedConfig.value.primaryDevice]
    if (selectedConfig.value.secondaryDevices) {
      selected.push(...selectedConfig.value.secondaryDevices)
    }
    return selected
  })

  const primaryDevice = computed(() => selectedConfig.value.primaryDevice)
  const secondaryDevices = computed(() => selectedConfig.value.secondaryDevices || [])
  const hardware = computed(() => devices.value)

  async function detectHardware() {
    isDetecting.value = true
    try {
      // This would be replaced with actual hardware detection logic
      const mockDevices: HardwareDevice[] = [
        {
          id: 'cpu',
          name: 'Intel Core i7-12700K',
          type: HardwareType.CPU,
          memory: 32,
          utilization: 15,
          temperature: 45,
          supported: true,
          selected: true
        },
        {
          id: 'intel_gpu_0',
          name: 'Intel Arc A770',
          type: HardwareType.INTEL_GPU,
          memory: 16,
          utilization: 25,
          temperature: 65,
          supported: true,
          selected: false
        },
        {
          id: 'intel_npu_0',
          name: 'Intel Ultra NPU',
          type: HardwareType.INTEL_NPU,
          memory: 4,
          utilization: 0,
          temperature: 40,
          supported: true,
          selected: false
        },
        {
          id: 'nvidia_gpu_0',
          name: 'NVIDIA RTX 4080',
          type: HardwareType.NVIDIA_GPU,
          memory: 16,
          utilization: 35,
          temperature: 70,
          supported: true,
          selected: false
        }
      ]
      
      devices.value = mockDevices
      
      // Set primary device if not already set
      if (!selectedConfig.value.primaryDevice) {
        selectedConfig.value.primaryDevice = mockDevices[0]
      }
    } catch (error) {
      console.error('Failed to detect hardware:', error)
    } finally {
      isDetecting.value = false
    }
  }

  function selectPrimaryDevice(device: HardwareDevice) {
    selectedConfig.value.primaryDevice = device
  }

  function addSecondaryDevice(device: HardwareDevice) {
    if (!selectedConfig.value.secondaryDevices) {
      selectedConfig.value.secondaryDevices = []
    }
    if (!selectedConfig.value.secondaryDevices.find(d => d.id === device.id)) {
      selectedConfig.value.secondaryDevices.push(device)
    }
  }

  function removeSecondaryDevice(deviceId: string) {
    if (selectedConfig.value.secondaryDevices) {
      selectedConfig.value.secondaryDevices = selectedConfig.value.secondaryDevices.filter(
        d => d.id !== deviceId
      )
    }
  }

  function setAccelerationMode(mode: 'single' | 'multi' | 'hybrid') {
    selectedConfig.value.mode = mode
  }

  function updateDeviceUtilization(deviceId: string, utilization: number) {
    const device = devices.value.find(d => d.id === deviceId)
    if (device) {
      device.utilization = utilization
    }
  }

  function updateDeviceTemperature(deviceId: string, temperature: number) {
    const device = devices.value.find(d => d.id === deviceId)
    if (device) {
      device.temperature = temperature
    }
  }

  function updateHardwareStatus(hardwareStatus: any) {
    if (hardwareStatus.devices) {
      devices.value = hardwareStatus.devices
    }
    if (hardwareStatus.primary_device) {
      selectedConfig.value.primaryDevice = hardwareStatus.primary_device
    }
  }

  return {
    devices,
    selectedConfig,
    isDetecting,
    availableDevices,
    selectedDevices,
    primaryDevice,
    secondaryDevices,
    hardware,
    detectHardware,
    selectPrimaryDevice,
    addSecondaryDevice,
    removeSecondaryDevice,
    setAccelerationMode,
    updateDeviceUtilization,
    updateDeviceTemperature,
    updateHardwareStatus
  }
})