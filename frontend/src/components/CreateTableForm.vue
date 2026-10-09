<template>
  <a-modal v-model:open="visible" title="新建表" width="720px" @ok="handleSubmit" :confirm-loading="submitting">
    <div style="margin-bottom: 12px; display: flex; gap: 8px">
      <a-radio-group v-model:value="mode" button-style="solid" size="small">
        <a-radio-button value="form">可视化</a-radio-button>
        <a-radio-button value="sql">SQL</a-radio-button>
      </a-radio-group>
    </div>

    <!-- SQL 模式 -->
    <template v-if="mode === 'sql'">
      <a-form layout="vertical">
        <a-form-item label="建表 SQL">
          <a-textarea
            v-model:value="rawSql"
            :rows="12"
            placeholder="CREATE TABLE example (&#10;  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,&#10;  name VARCHAR(255) NOT NULL&#10;) COMMENT='示例表';"
            style="font-family: monospace; font-size: 13px"
          />
        </a-form-item>
      </a-form>
    </template>

    <!-- 可视化模式 -->
    <template v-else>
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="数据库"><a-input :value="database" disabled /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="表名"><a-input v-model:value="tableName" placeholder="table_name" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="表注释"><a-input v-model:value="tableComment" /></a-form-item>

        <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
          <strong>字段定义</strong>
          <a-button size="small" type="dashed" @click="addColumn">+ 添加字段</a-button>
        </div>

        <a-table :data-source="columns" :pagination="false" size="small" bordered>
          <a-table-column title="字段名" data-index="name">
            <template #default="{ record }"><a-input v-model:value="record.name" size="small" /></template>
          </a-table-column>
          <a-table-column title="类型" data-index="type" width="160">
            <template #default="{ record }">
              <a-select v-model:value="record.type" size="small" show-search style="width: 100%">
                <a-select-option v-for="t in commonTypes" :key="t" :value="t">{{ t }}</a-select-option>
              </a-select>
            </template>
          </a-table-column>
          <a-table-column title="可空" width="60" align="center">
            <template #default="{ record }"><a-checkbox v-model:checked="record.nullable" /></template>
          </a-table-column>
          <a-table-column title="主键" width="60" align="center">
            <template #default="{ record }"><a-checkbox v-model:checked="record.primary_key" /></template>
          </a-table-column>
          <a-table-column title="自增" width="60" align="center">
            <template #default="{ record }"><a-checkbox v-model:checked="record.auto_increment" /></template>
          </a-table-column>
          <a-table-column title="默认值" width="120">
            <template #default="{ record }"><a-input v-model:value="record.default_value" size="small" placeholder="NULL" /></template>
          </a-table-column>
          <a-table-column title="" width="50" align="center">
            <template #default="{ index }">
              <a-button type="text" danger size="small" @click="columns.splice(index, 1)">✕</a-button>
            </template>
          </a-table-column>
        </a-table>
      </a-form>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { ddlApi, queryApi, type ColumnDef } from '@/api'

const props = defineProps<{ connId: string; database: string }>()
const emit = defineEmits<{ created: [] }>()

const visible = defineModel<boolean>({ default: false })
const submitting = ref(false)
const tableName = ref('')
const tableComment = ref('')
const mode = ref<'form' | 'sql'>('form')
const rawSql = ref('')

const commonTypes = [
  'INT', 'BIGINT', 'SMALLINT', 'TINYINT',
  'VARCHAR(255)', 'VARCHAR(64)', 'TEXT', 'LONGTEXT',
  'DECIMAL(10,2)', 'FLOAT', 'DOUBLE',
  'DATETIME', 'TIMESTAMP', 'DATE',
  'BOOLEAN', 'JSON',
]

const columns = ref<ColumnDef[]>([
  { name: 'id', type: 'BIGINT', nullable: false, primary_key: true, auto_increment: true, default_value: null, comment: null },
])

function addColumn() {
  columns.value.push({ name: '', type: 'VARCHAR(255)', nullable: true, primary_key: false, auto_increment: false, default_value: null, comment: null })
}

function resetForm() {
  tableName.value = ''
  tableComment.value = ''
  columns.value = [{ name: 'id', type: 'BIGINT', nullable: false, primary_key: true, auto_increment: true, default_value: null, comment: null }]
  rawSql.value = ''
  mode.value = 'form'
}

async function handleSubmit() {
  if (mode.value === 'sql') {
    const sql = rawSql.value.trim()
    if (!sql) { message.warning('请输入建表 SQL'); return }
    submitting.value = true
    try {
      await queryApi.execute(props.connId, sql, props.database)
      message.success('建表成功')
      visible.value = false
      resetForm()
      emit('created')
    } catch (e: any) {
      message.error(e.message)
    } finally {
      submitting.value = false
    }
    return
  }

  // 可视化模式
  if (!tableName.value) { message.warning('请输入表名'); return }
  if (columns.value.length === 0) { message.warning('至少需要一个字段'); return }
  submitting.value = true
  try {
    await ddlApi.createTable({
      conn_id: props.connId,
      database: props.database,
      table: tableName.value,
      columns: columns.value,
      comment: tableComment.value || undefined,
    })
    message.success('建表成功')
    visible.value = false
    resetForm()
    emit('created')
  } catch (e: any) {
    message.error(e.message)
  } finally {
    submitting.value = false
  }
}

function open() {
  resetForm()
  visible.value = true
}

defineExpose({ open })
</script>
