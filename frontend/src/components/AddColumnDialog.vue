<template>
  <a-modal v-model:open="visible" title="添加字段" @ok="handleSubmit" :confirm-loading="submitting">
    <a-form layout="vertical">
      <a-form-item label="字段名"><a-input v-model:value="col.name" /></a-form-item>
      <a-form-item label="类型">
        <a-select v-model:value="col.type" show-search>
          <a-select-option v-for="t in types" :key="t" :value="t">{{ t }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-row :gutter="16">
        <a-col :span="8"><a-checkbox v-model:checked="col.nullable">可空</a-checkbox></a-col>
        <a-col :span="8"><a-checkbox v-model:checked="col.primary_key">主键</a-checkbox></a-col>
        <a-col :span="8"><a-checkbox v-model:checked="col.auto_increment">自增</a-checkbox></a-col>
      </a-row>
      <a-form-item label="默认值" style="margin-top: 12px"><a-input v-model:value="col.default_value" placeholder="留空为 NULL" /></a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { ddlApi, type ColumnDef } from '@/api'

const props = defineProps<{ connId: string; database: string; table: string }>()
const emit = defineEmits<{ added: [] }>()

const visible = defineModel<boolean>({ default: false })
const submitting = ref(false)

const types = ['INT', 'BIGINT', 'VARCHAR(255)', 'VARCHAR(64)', 'TEXT', 'DECIMAL(10,2)', 'DATETIME', 'TIMESTAMP', 'BOOLEAN', 'JSON']

const col = reactive<ColumnDef>({
  name: '', type: 'VARCHAR(255)', nullable: true, primary_key: false, auto_increment: false, default_value: null, comment: null,
})

async function handleSubmit() {
  if (!col.name) { message.warning('请输入字段名'); return }
  submitting.value = true
  try {
    await ddlApi.addColumn({ conn_id: props.connId, database: props.database, table: props.table, column: { ...col } })
    message.success('添加成功')
    visible.value = false
    emit('added')
  } catch (e: any) {
    message.error(e.message)
  } finally {
    submitting.value = false
  }
}
</script>
