<template>
  <div class="terminal-instance-wrapper" v-show="visible">
    <div ref="terminalRef" class="xterm-box"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

const props = defineProps({
  hostId: { type: Number, required: true },
  hostName: { type: String, required: true },
  visible: { type: Boolean, default: true }
});

const emit = defineEmits(['connected', 'disconnected']);

const terminalRef = ref<HTMLElement | null>(null);
let term: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let ws: WebSocket | null = null;

const initTerminal = () => {
  const bodyColor = getComputedStyle(document.documentElement).getPropertyValue('--app-bg-color').trim() || '#121212';
  const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() || '#e0e0e0';
  const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#00ff00';

  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: { 
      background: bodyColor, 
      foreground: textColor,
      cursor: primaryColor,
      selectionBackground: primaryColor + '66', // 40% opacity
    },
    allowProposedApi: true
  });

  fitAddon = new FitAddon();
  term.loadAddon(fitAddon);

  if (terminalRef.value) {
    term.open(terminalRef.value);
    fitAddon.fit();
  }

  connectWS();

  term.onData(data => {
    if (ws?.readyState === WebSocket.OPEN) ws.send(data);
  });
};

const connectWS = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/api/terminal/ws/${props.hostId}`);

  ws.onopen = () => {
    emit('connected');
    term?.write(`\x1b[32m[系统] 已连接至 ${props.hostName}\x1b[0m\r\n`);
    fitAddon?.fit();
  };

  ws.onmessage = e => term?.write(e.data);
  ws.onclose = () => {
    emit('disconnected');
    term?.write('\r\n\x1b[31m[系统] 会话已断开\x1b[0m\r\n');
  };
};

// 暴露给父组件的方法
const fit = () => fitAddon?.fit();
const write = (data: string) => term?.write(data);
const send = (data: string) => ws?.readyState === WebSocket.OPEN && ws.send(data);
const focus = () => term?.focus();
const clear = () => term?.clear();
const reconnect = () => {
  if (ws) ws.close();
  term?.reset();
  connectWS();
};

defineExpose({ fit, write, send, focus, clear, reconnect });

// 当组件变为可见时，重新自适应大小
watch(() => props.visible, (newVal) => {
  if (newVal) {
    setTimeout(() => {
      fitAddon?.fit();
      term?.focus();
    }, 50);
  }
});

onMounted(() => {
  setTimeout(initTerminal, 100);
  window.addEventListener('resize', fit);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', fit);
  if (ws) ws.close();
  if (term) term.dispose();
});
</script>

<style scoped>
.terminal-instance-wrapper {
  height: 100%;
  width: 100%;
  background: var(--app-bg-color);
  padding: 8px; /* 给文字留出一点点边缘，不至于太死板 */
  box-sizing: border-box;
}
.xterm-box {
  height: 100%;
  width: 100%;
}
</style>
