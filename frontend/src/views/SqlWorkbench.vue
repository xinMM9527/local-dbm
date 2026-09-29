<template>
  <a-layout style="height: 100vh">
    <!-- Header -->
    <a-layout-header style="background: #fff; padding: 0 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #f0f0f0; height: 48px; line-height: 48px">
      <h3 style="margin: 0; white-space: nowrap">DBM</h3>
      <a-select v-model:value="connStore.currentId" style="width: 200px" placeholder="选择连接" @change="onConnectionChange">
        <a-select-option v-for="c in connStore.connections" :key="c.id!" :value="c.id!">{{ c.name }}</a-select-option>
      </a-select>
      <a-select v-if="databases.length" v-model:value="currentDb" style="width: 160px" placeholder="选择数据库">
        <a-select-option v-for="db in databases" :key="db" :value="db">{{ db }}</a-select-option>
      </a-select>
      <div style="flex: 1" />
      <a-button size="small" @click="showCreateTable = true">新建表</a-button>
      <router-link to="/connections"><a-button size="small">连接管理</a-button></router-link>
    </a-layout-header>

    <a-layout>
      <!-- Sidebar: Schema Tree -->
      <a-layout-sider width="240" theme="light" style="border-right: 1px solid #f0f0f0">
        <SchemaTree @select-table="onSelectTable" />
      </a-layout-sider>

      <!-- Main Content -->
      <a-layout-content style="display: flex; flex-direction: column; min-height: 0">
        <!-- SQL Editor -->
        <div style="flex: 1; min-height: 200px; border-bottom: 1px solid #f0f0f0">
          <SqlEditor v-model="sqlCode" :executing="executing" :last-duration="lastDuration" @execute="handleExecute" />
        </div>

        <!-- Results / Table Info -->
        <div style="flex: 1; min-height: 200px; overflow: hidden">
          <a-tabs v-model:activeKey="bottomTab" size="small" style="height: 100%; padding: 0 8px">
            <a-tab-pane key="results" tab="查询结果">
              <ResultTable :results="queryResults" />
            </a-tab-pane>
            <a-tab-pane key="structure" tab="表结构">
              <div v-if="selectedTable" style="padding: 8px; overflow: auto; height: 100%">
                <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
                  <strong>{{ selectedTable.db }}.{{ selectedTable.table }}</strong>
                  <a-button size="small" type="dashed" @click="showAddColumn = true">+ 添加字段</a-button>
                </div>
                <a-table :data-source="tableColumns" :columns="columnTableCols" size="small" bordered :pagination="false" />
              </div>
              <a-empty v-else description="从左侧选择一张表" style="margin-top: 40px" />
            </a-tab-pane>
            <a-tab-pane key="history" tab="执行历史">
              <div style="padding: 8px; overflow: auto; height: 100%">
                <a-list :data-source="historyStore.history" size="small">
                  <template #renderItem="{ item }">
                    <a-list-item style="cursor: pointer; padding: 4px 8px" @click="sqlCode = item.sql">
                      <code style="font-size: 12px">{{ item.sql.substring(0, 120) }}{{ item.sql.length > 120 ? '...' : '' }}</code>
                      <span style="color: #999; font-size: 11px; margin-left: 8px">{{ item.timestamp }}</span>
                    </a-list-item>
                  </template>
                </a-list>
                <a-button v-if="historyStore.history.length" size="small" danger style="margin-top: 8px" @click="historyStore.clear()">清空历史</a-button>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </a-layout-content>
    </a-layout>

    <!-- Dialogs -->
    <CreateTableForm v-if="connStore.currentId && currentDb" v-model="showCreateTable" :conn-id="connStore.currentId" :database="currentDb" @created="refreshSchema" />
    <AddColumnDialog v-if="selectedTable" v-model="showAddColumn" :conn-id="connStore.currentId!" :database="selectedTable.db" :table="selectedTable.table" @added="loadTableStructure" />
  </a-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useConnectionStore } from '@/stores/connection'
import { useQueryHistoryStore } from '@/stores/queryHistory'
import { schemaApi, queryApi, type QueryResult, type ColumnInfo } from '@/api'
import SchemaTree from '@/components/SchemaTree.vue'
import SqlEditor from '@/components/SqlEditor.vue'
import ResultTable from '@/components/ResultTable.vue'
import CreateTableForm from '@/components/CreateTableForm.vue'
import AddColumnDialog from '@/components/AddColumnDialog.vue'

const connStore = useConnectionStore()
const historyStore = useQueryHistoryStore()

const databases = ref<string[]>([])
const currentDb = ref<string>('')
const sqlCode = ref('')
const executing = ref(false)
const lastDuration = ref<number | null>(null)
const queryResults = ref<QueryResult[]>([])
const bottomTab = ref('results')

const selectedTable = ref<{ db: string; table: string } | null>(null)
const tableColumns = ref<ColumnInfo[]>([])
const showCreateTable = ref(false)
const showAddColumn = ref(false)

const columnTableCols = [
  { title: '字段名', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '可空', dataIndex: 'nullable', key: 'nullable', customRender: ({ text }: any) => text ? '✓' : '' },
  { title: '主键', dataIndex: 'is_primary_key', key: 'pk', customRender: ({ text }: any) => text ? '✓' : '' },
  { title: '默认值', dataIndex: 'default_value', key: 'default' },
  { title: '注释', dataIndex: 'comment', key: 'comment' },
]

onMounted(async () => {
  await connStore.fetchConnections()
  await historyStore.fetchHistory()
  if (connStore.currentId) loadDatabases(connStore.currentId)
})

async function loadDatabases(connId: string) {
  try {
    databases.value = await schemaApi.databases(connId)
    if (databases.value.length && !currentDb.value) currentDb.value = databases.value[0]
  } catch { databases.value = [] }
}

function onConnectionChange(connId: string) {
  currentDb.value = ''
  databases.value = []
  selectedTable.value = null
  tableColumns.value = []
  loadDatabases(connId)
}

async function onSelectTable(db: string, table: string) {
  selectedTable.value = { db, table }
  currentDb.value = db
  bottomTab.value = 'structure'
  await loadTableStructure()
}

async function loadTableStructure() {
  if (!selectedTable.value || !connStore.currentId) return
  try {
    tableColumns.value = await schemaApi.columns(connStore.currentId, selectedTable.value.db, selectedTable.value.table)
  } catch (e: any) {
    message.error(e.message)
  }
}

async function handleExecute(sql: string) {
  if (!connStore.currentId) { message.warning('请先选择连接'); return }
  if (!sql.trim()) { message.warning('请输入 SQL'); return }
  executing.value = true
  lastDuration.value = null
  try {
    const results = await queryApi.execute(connStore.currentId, sql, currentDb.value || undefined)
    queryResults.value = results
    lastDuration.value = results.reduce((sum, r) => sum + r.duration_ms, 0)
    bottomTab.value = 'results'
    await historyStore.fetchHistory()
    // Refresh schema if DDL was executed
    if (results.some((r) => r.message === 'OK')) {
      await refreshSchema()
    }
  } catch (e: any) {
    message.error(e.message)
  } finally {
    executing.value = false
  }
}

async function refreshSchema() {
  if (connStore.currentId) {
    await loadDatabases(connStore.currentId)
    if (selectedTable.value) await loadTableStructure()
  }
}

watch(currentDb, () => {
  selectedTable.value = null
  tableColumns.value = []
})
</script>
