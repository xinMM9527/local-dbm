<template>
  <div style="padding: 24px; max-width: 800px; margin: 0 auto">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h2 style="margin: 0">连接管理</h2>
      <a-button type="primary" @click="showModal()">新增连接</a-button>
    </div>

    <a-spin :spinning="store.loading">
      <a-list :data-source="store.connections" item-layout="horizontal">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.name" :description="`${item.type.toUpperCase()} · ${item.host}:${item.port}/${item.database}`" />
            <template #actions>
              <a-button size="small" @click="handleTest(item.id!)" :loading="testingId === item.id">测试</a-button>
              <a-button size="small" @click="showModal(item)">编辑</a-button>
              <a-popconfirm title="确认删除？" @confirm="store.deleteConnection(item.id!)">
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </template>
          </a-list-item>
        </template>
      </a-list>
      <a-empty v-if="!store.loading && store.connections.length === 0" description="暂无连接，点击右上角添加" />
    </a-spin>

    <a-modal v-model:open="modalVisible" :title="editingId ? '编辑连接' : '新增连接'" @ok="handleSubmit" :confirm-loading="submitting">
      <a-form :model="form" layout="vertical">
        <a-form-item label="连接名称"><a-input v-model:value="form.name" placeholder="My Database" /></a-form-item>
        <a-form-item label="数据库类型">
          <a-select v-model:value="form.type">
            <a-select-option value="mysql">MySQL</a-select-option>
            <a-select-option value="postgresql">PostgreSQL</a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="16"><a-form-item label="主机"><a-input v-model:value="form.host" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="端口"><a-input-number v-model:value="form.port" style="width: 100%" /></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="用户名"><a-input v-model:value="form.username" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="密码"><a-input-password v-model:value="form.password" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="默认数据库"><a-input v-model:value="form.database" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { useConnectionStore } from '@/stores/connection'
import type { ConnectionConfig } from '@/api'

const store = useConnectionStore()
const modalVisible = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const testingId = ref<string | null>(null)

const defaultForm = (): ConnectionConfig => ({
  name: '', type: 'mysql', host: '127.0.0.1', port: 3306, username: 'root', password: '', database: '',
})
const form = reactive(defaultForm())

onMounted(() => store.fetchConnections())

function showModal(item?: ConnectionConfig) {
  if (item) {
    editingId.value = item.id!
    Object.assign(form, item)
  } else {
    editingId.value = null
    Object.assign(form, defaultForm())
  }
  modalVisible.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (editingId.value) {
      await store.updateConnection(editingId.value, { ...form })
      message.success('更新成功')
    } else {
      await store.addConnection({ ...form })
      message.success('创建成功')
    }
    modalVisible.value = false
  } catch (e: any) {
    message.error(e.message)
  } finally {
    submitting.value = false
  }
}

async function handleTest(id: string) {
  testingId.value = id
  try {
    await store.testConnection(id)
    message.success('连接成功')
  } catch (e: any) {
    message.error(`连接失败: ${e.message}`)
  } finally {
    testingId.value = null
  }
}
</script>
