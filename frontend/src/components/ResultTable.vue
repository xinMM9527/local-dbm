<template>
  <div style="height: 100%; overflow: auto">
    <template v-if="results.length === 0">
      <a-empty description="执行 SQL 查看结果" style="margin-top: 40px" />
    </template>

    <a-tabs v-else v-model:activeKey="activeTab" size="small" style="padding: 0 8px">
      <a-tab-pane v-for="(r, i) in results" :key="i" :tab="`结果 ${i + 1}`">
        <div style="margin-bottom: 8px; font-size: 12px; color: #999">
          {{ r.sql }} · {{ r.duration_ms }}ms
          <template v-if="r.affected_rows !== undefined"> · 影响 {{ r.affected_rows }} 行</template>
        </div>

        <template v-if="r.columns && r.rows">
          <a-table
            :columns="r.columns.map((c: string) => ({ title: c, dataIndex: c, key: c, ellipsis: true }))"
            :data-source="rowsToObjects(r)"
            :pagination="{ pageSize: 50, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
            size="small"
            bordered
            scroll-x="max-content"
          />
        </template>
        <template v-else>
          <a-result :status="'success'" :title="r.message || '执行成功'" />
        </template>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { QueryResult } from '@/api'

defineProps<{ results: QueryResult[] }>()
const activeTab = ref(0)

function rowsToObjects(r: QueryResult) {
  if (!r.columns || !r.rows) return []
  return r.rows.map((row) => {
    const obj: Record<string, any> = {}
    r.columns!.forEach((col, i) => { obj[col] = row[i] })
    return obj
  })
}
</script>
