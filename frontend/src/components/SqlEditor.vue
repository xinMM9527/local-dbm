<template>
  <div style="height: 100%; display: flex; flex-direction: column">
    <div style="flex: 1; min-height: 0">
      <vue-monaco-editor
        v-model:value="code"
        language="sql"
        :theme="theme"
        :options="editorOptions"
        @mount="onMount"
      />
    </div>
    <div style="padding: 8px; border-top: 1px solid #f0f0f0; display: flex; gap: 8px; align-items: center">
      <a-button type="primary" @click="$emit('execute', code)" :loading="executing">
        ▶ 执行 (Ctrl+Enter)
      </a-button>
      <span v-if="lastDuration !== null" style="color: #999; font-size: 12px">{{ lastDuration }}ms</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

defineProps<{
  executing?: boolean
  lastDuration?: number | null
}>()

const emit = defineEmits<{
  execute: [sql: string]
}>()

const code = defineModel<string>({ default: '' })
const theme = ref('vs')

const editorOptions = {
  minimap: { enabled: false },
  fontSize: 14,
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
}

function onMount(editor: any) {
  editor.addCommand(
    // Ctrl+Enter
    // eslint-disable-next-line no-bitwise
    2048 | 3, // KeyMod.CtrlCmd | KeyCode.Enter
    () => emit('execute', code.value),
  )
}
</script>
