<template>
  <div class="ai-chat-module">
    <n-card :bordered="false" class="chat-card" title="AI 对话" content-style="display: flex; flex-direction: column; height: 100%;">
      <template #header-extra>
        <n-button size="tiny" secondary type="error" @click="clearHistory" v-if="messages.length > 0">
          清空对话
        </n-button>
      </template>
      <div class="chat-window" ref="chatWindow">
        <div v-if="messages.length === 0" class="empty-state">
          <n-empty description="开始一次新的对话吧" />
        </div>
        
        <div v-for="(msg, index) in messages" :key="index" :class="['message-bubble', msg.role]">
          <div class="message-content">
            <div v-if="msg.role === 'assistant'" class="sender-name">AI</div>
            <div v-else class="sender-name">You</div>
            <div class="text" v-html="formatMessage(msg.content)"></div>
          </div>
        </div>
        
        <div v-if="loading" class="message-bubble assistant">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <n-input
          type="textarea"
          v-model:value="userInput" 
          :autosize="{ minRows: 2, maxRows: 6 }"
          placeholder="输入你的问题... (Ctrl+Enter 发送)"
          @keydown.enter="handleEnter"
          :disabled="loading"
        />
        <n-button type="primary" circle @click="sendMessage" :loading="loading" class="send-btn">
          <template #icon><n-icon><SendIcon /></n-icon></template>
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ScienceOutlined as SendIcon } from '@vicons/material'
import { useMessage, NCard, NEmpty, NInput, NButton, NIcon } from 'naive-ui'

const message = useMessage()

const formatMessage = (text: string) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

const props = defineProps<{
  systemPrompt?: string
}>()

const messages = ref<{role: string, content: string}[]>([])
const userInput = ref('')
const loading = ref(false)
const chatWindow = ref<HTMLElement | null>(null)

const clearHistory = () => {
  messages.value = []
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatWindow.value) {
    chatWindow.value.scrollTop = chatWindow.value.scrollHeight
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.ctrlKey) {
    e.preventDefault() // Prevent newline
    sendMessage()
  }
}

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return
  
  const userMsg = userInput.value.trim()
  messages.value.push({ role: 'user', content: userMsg })
  userInput.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const context = messages.value.map(m => ({ role: m.role, content: m.content }))
    if (props.systemPrompt) {
      context.unshift({ role: 'system', content: props.systemPrompt })
    }

    // 使用 fetch 获取流式响应
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: context })
    })

    if (!response.ok) throw new Error('Network error')
    if (!response.body) throw new Error('No response body')

    const assistantMsg = { role: 'assistant', content: '' }
    messages.value.push(assistantMsg)
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      assistantMsg.content += text
      scrollToBottom()
    }

  } catch (e) {
    message.error('发送失败: ' + String(e))
    messages.value.push({ role: 'assistant', content: '[Error: Request Failed]' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-card {
  height: 75vh;
}

.chat-window {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  margin-bottom: 10px;
  /* Ensure it takes available space inside card content */
  height: 100%; 
}

/* Dark mode adjustment for chat background */
:deep(.n-card.n-card--bordered) .chat-window,
:deep(.n-card) .chat-window {
    background-color: rgba(0, 0, 0, 0.05);
}

.message-bubble {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.message-bubble.user {
  align-items: flex-end;
}

.message-bubble.assistant {
  align-items: flex-start;
}

.sender-name {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  margin-left: 4px;
}

.user .sender-name {
  margin-right: 4px;
}

.message-content {
  max-width: 80%;
}

.text {
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user .text {
  background: #18a058; /* Naive UI primary green-ish */
  color: white;
  border-bottom-right-radius: 2px;
}

.assistant .text {
  background: #fff;
  border: 1px solid #eee;
  border-bottom-left-radius: 2px;
  color: #333;
}

.input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  margin-top: auto; /* Push to bottom if needed */
}

.send-btn {
  margin-bottom: 4px;
}

.typing-indicator span {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #ccc;
  border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>