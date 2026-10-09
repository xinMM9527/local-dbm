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
  /** Full unfiltered table children, kept for client-side search filtering */
  allChildren?: TreeNode[]
}

const treeData = ref<TreeNode[]>([])

watch(() => store.currentId, async (connId) => {
  if (!connId) { treeData.value = []; return }
  loading.value = true
  try {
    const dbs = await schemaApi.databases(connId)
    const nodes: TreeNode[] = await Promise.all(
      dbs.map(async (db) => {
        let children: TreeNode[] = []
        try {
          const tables = await schemaApi.tables(connId, db)
          children = tables.map((t) => ({
            title: t, key: `${db}.${t}`, isLeaf: true, db, table: t,
          }))
        } catch {
          // ignore single-db failure; still show the db node
        }
        return {
          title: db, key: `db:${db}`, isLeaf: false, db,
          children, allChildren: children,
        }
      }),
    )
    treeData.value = nodes
  } catch {
    treeData.value = []
  } finally {
    loading.value = false
  }
}, { immediate: true })

async function onLoadData(node: TreeNode) {
  const connId = store.currentId!
  if (node.db && !node.table && !node.allChildren) {
    // Fallback lazy load if allChildren was not populated
    const tables = await schemaApi.tables(connId, node.db)
    const children = tables.map((t) => ({
      title: t, key: `${node.db}.${t}`, isLeaf: true, db: node.db, table: t,
    }))
    node.children = children
    node.allChildren = children
  }
}

function onSelect(keys: string[], info: any) {
  selectedKeys.value = keys
  const node = info.node as TreeNode
  if (node.db && node.table) {
    emit('selectTable', node.db, node.table)
  }
}

// Client-side filter over pre-loaded tables; no extra API calls
watch(searchText, () => {
  const keyword = searchText.value.toLowerCase()
  for (const dbNode of treeData.value) {
    if (!dbNode.allChildren) continue
    dbNode.children = keyword
      ? dbNode.allChildren.filter((c) => c.title.toLowerCase().includes(keyword))
      : dbNode.allChildren
  }
})
</script>
