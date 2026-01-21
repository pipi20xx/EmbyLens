<template>
  <n-modal
    :show="show"
    @update:show="$emit('update:show', $event)"
    preset="card"
    :title="`容器终端: ${containerName}`"
    style="width: 90vw; max-width: 1000px"
    @after-enter="initTerminal"
    @after-leave="destroyTerminal"
  >
    <div ref="terminalRef" class="terminal-container"></div>
    <template #footer>
      <n-space justify="space-between">
        <n-text depth="3">提示: 输入 `exit` 或关闭窗口退出终端</n-text>
        <n-button size="small" @click="$emit('update:show', false)">关闭</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { NModal, NSpace, NButton, NText } from 'naive-ui'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

const props = defineProps({
  show: Boolean,
  hostId: String,
  containerId: String,
  containerName: String,
  command: String
})

const emit = defineEmits(['update:show'])

const terminalRef = ref<HTMLElement | null>(null)
let term: Terminal | null = null
let fitAddon: FitAddon | null = null
let ws: WebSocket | null = null

const initTerminal = () => {
  if (!terminalRef.value) return

  term = new Terminal({
    cursorBlink: true,
    fontFamily: '"Fira Code", monospace',
    fontSize: 14,
    theme: {
      background: '#1e1e1e'
    }
  })

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalRef.value)
  fitAddon.fit()
  term.focus() // 强制获取焦点

  term.writeln('\x1b[1;32mConnecting to container terminal...\x1b[0m')

  // 建立 WebSocket 连接
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const shell = props.command || '/bin/bash'
  ws = new WebSocket(`${protocol}//${host}/api/docker/${props.hostId}/containers/${props.containerId}/exec?command=${shell}`)

  ws.onopen = () => {
    // 处理用户输入
    term?.onData(data => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    })
  }

  ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      const reader = new FileReader()
      reader.onload = () => {
        term?.write(new Uint8Array(reader.result as ArrayBuffer))
      }
      reader.readAsArrayBuffer(event.data)
    } else {
      term?.write(event.data)
    }
  }

  ws.onclose = () => {
    term?.writeln('\r\n\x1b[1;31mTerminal session closed.\x1b[0m')
  }

  ws.onerror = () => {
    term?.writeln('\r\n\x1b[1;31mConnection error.\x1b[0m')
  }

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  fitAddon?.fit()
}

const destroyTerminal = () => {
  window.removeEventListener('resize', handleResize)
  ws?.close()
  term?.dispose()
  term = null
  ws = null
}

onBeforeUnmount(destroyTerminal)
</script>

<style scoped>
.terminal-container {
  height: 500px;
  background: #1e1e1e;
  padding: 10px;
  border-radius: 4px;
}

:deep(.xterm-viewport) {
  background-color: #1e1e1e !important;
}
</style>
