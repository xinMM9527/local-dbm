import { defineStore } from 'pinia'
import { ref } from 'vue'
import { queryApi } from '@/api'

export const useQueryHistoryStore = defineStore('queryHistory', () => {
  const history = ref<{ sql: string; timestamp: string }[]>([])

  async function fetchHistory() {
    history.value = await queryApi.history()
  }

  async function clear() {
    await queryApi.clearHistory()
    history.value = []
  }

  return { history, fetchHistory, clear }
})
