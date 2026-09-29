<template>
  <div style="height: 100%; overflow: auto; padding: 8px">
    <a-input-search v-model:value="searchText" placeholder="搜索表名..." size="small" style="margin-bottom: 8px" allow-clear />
    <a-spin :spinning="loading">
      <a-tree
        v-if="treeData.length"
        :tree-data="treeData"
        :load-data="onLoadData"
        :selected-keys="selectedKeys"
        @select="onSelect"
        show-icon
        block-node
      />
      <a-empty v-else description="请选择连接" :image-style="{ height: '40px' }" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { schemaApi } from '@/api'
import { useConnectionStore } from '@/stores/connection'
import { DatabaseOutlined, TableOutlined } from '@ant-design/icons-vue'

const emit = defineEmits<{
  selectTable: [db: string, table: string]
}>()

const store = useConnectionStore()
const loading = ref(false)
const searchText = ref('')
const selectedKeys = ref<string[]>([])

interface TreeNode {
  title: string
  key: string
  isLeaf?: boolean
  children?: TreeNode[]
  db?: string
  table?: string
}

const treeData = ref<TreeNode[]>([])

watch(() => store.currentId, async (connId) => {
  if (!connId) { treeData.value = []; return }
  loading.value = true
  try {
    const dbs = await schemaApi.databases(connId)
    treeData.value = dbs.map((db) => ({
      title: db, key: `db:${db}`, isLeaf: false, db,
    }))
  } catch {
    treeData.value = []
  } finally {
    loading.value = false
  }
}, { immediate: true })

async function onLoadData(node: TreeNode) {
  const connId = store.currentId!
  if (node.db && !node.table) {
    // Load tables
    const tables = await schemaApi.tables(connId, node.db)
    const filtered = searchText.value
      ? tables.filter((t) => t.toLowerCase().includes(searchText.value.toLowerCase()))
      : tables
    node.children = filtered.map((t) => ({
      title: t, key: `${node.db}.${t}`, isLeaf: true, db: node.db, table: t,
    }))
  }
}

function onSelect(keys: string[], info: any) {
  selectedKeys.value = keys
  const node = info.node as TreeNode
  if (node.db && node.table) {
    emit('selectTable', node.db, node.table)
  }
}

// Re-filter when search text changes
watch(searchText, async () => {
  const connId = store.currentId
  if (!connId || treeData.value.length === 0) return
  for (const dbNode of treeData.value) {
    if (dbNode.db) {
      const tables = await schemaApi.tables(connId, dbNode.db)
      const filtered = searchText.value
        ? tables.filter((t) => t.toLowerCase().includes(searchText.value.toLowerCase()))
        : tables
      dbNode.children = filtered.map((t) => ({
        title: t, key: `${dbNode.db}.${t}`, isLeaf: true, db: dbNode.db, table: t,
      }))
    }
  }
})
</script>
