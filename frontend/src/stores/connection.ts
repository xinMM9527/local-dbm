import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { connectionApi, type ConnectionConfig } from '@/api'

export const useConnectionStore = defineStore('connection', () => {
  const connections = ref<ConnectionConfig[]>([])
  const currentId = ref<string | null>(null)
  const loading = ref(false)

  const currentConnection = computed(() =>
    connections.value.find((c) => c.id === currentId.value) || null
  )

  async function fetchConnections() {
    loading.value = true
    try {
      connections.value = await connectionApi.list()
      if (!currentId.value && connections.value.length > 0) {
        currentId.value = connections.value[0].id!
      }
    } finally {
      loading.value = false
    }
  }

  async function addConnection(config: ConnectionConfig) {
    await connectionApi.create(config)
    await fetchConnections()
  }

  async function updateConnection(id: string, config: ConnectionConfig) {
    await connectionApi.update(id, config)
    await fetchConnections()
  }

  async function deleteConnection(id: string) {
    await connectionApi.delete(id)
    if (currentId.value === id) currentId.value = null
    await fetchConnections()
  }

  async function testConnection(id: string) {
    return connectionApi.test(id)
  }

  function setCurrent(id: string) {
    currentId.value = id
  }

  return {
    connections,
    currentId,
    currentConnection,
    loading,
    fetchConnections,
    addConnection,
    updateConnection,
    deleteConnection,
    testConnection,
    setCurrent,
  }
})
