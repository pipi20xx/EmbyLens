import { ref } from 'vue'
import { useMessage } from 'naive-ui'

export function useBookmarkAI(bookmarkApi: any, actions: any) {
  const message = useMessage()
  const isOrganizing = ref(false)

  const handleAIAnalyze = async () => {
    if (isOrganizing.value) return
    
    isOrganizing.value = true
    // 仅通过简单的非阻塞消息提示开始
    message.info('AI 整理已在后台启动，详细进度请查看浏览器控制台或系统日志', { duration: 5000 })
    
    try {
      const response = await fetch('/api/bookmarks/ai-auto-organize', {
        method: 'POST',
      })

      if (!response.ok) throw new Error('网络请求失败')
      if (!response.body) throw new Error('未收到后台响应')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      console.log('--- 🤖 AI 书签整理日志开始 ---')

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const statusText = line.replace('data: ', '').trim()
            // 实时打印每一条详细的移动日志到控制台
            console.log(`[AI] ${statusText}`)
          }
        }
      }

      console.log('--- ✅ AI 书签整理全部完成 ---')
      message.success('AI 整理已全部完成！')
      
      // 任务结束后，刷新一下 UI 的树结构
      await actions.refreshCurrentFolder()
    } catch (err: any) {
      console.error('[AI Error]', err)
      message.error('AI 整理任务异常: ' + err.message)
    } finally {
      isOrganizing.value = false
    }
  }

  return {
    handleAIAnalyze,
    isOrganizing
  }
}
