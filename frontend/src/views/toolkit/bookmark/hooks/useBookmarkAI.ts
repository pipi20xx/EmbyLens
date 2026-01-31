import { ref, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'

export function useBookmarkAI(bookmarkApi: any, actions: any, state: any) {
  const message = useMessage()
  const dialog = useDialog()
  const isOrganizing = ref(false)

  const handleAIAnalyze = async () => {
    if (isOrganizing.value) return
    
    // 获取当前选中的文件夹 ID
    const selectedFolderId = state.selectedKeys.value[0]
    const targetFolderId = (selectedFolderId === 'root' || !selectedFolderId) ? null : selectedFolderId
    const targetFolderName = targetFolderId ? actions.findItemById(state.bookmarks.value, targetFolderId)?.title : '全部书签'

    dialog.warning({
      title: 'AI 智能整理确认',
      content: () => h('div', null, [
        h('p', { style: 'font-weight: bold; font-size: 15px; margin-bottom: 8px;' }, 
          `范围：${targetFolderName}`
        ),
        h('p', null, 'AI 将会自动执行以下操作：'),
        h('ul', { style: 'margin-top: 5px; color: #aaa; font-size: 13px; line-height: 1.6;' }, [
          h('li', null, '规范化标题：去除冗余后缀（如“- 百度搜索”）。'),
          h('li', null, '智能分类：将书签自动搬运至更合理的文件夹。'),
          h('li', null, '自动清理：任务完成后将递归删除变空的旧目录。')
        ]),
        h('p', { style: 'margin-top: 12px; color: var(--primary-color); opacity: 0.8; font-size: 13px;' }, 
          '💡 小贴士：你可以先点击左侧目录树选中特定文件夹，再点击此按钮进行局部处理。'
        )
      ]),
      positiveText: '开始全自动整理',
      negativeText: '取消',
      onPositiveClick: () => {
        // 立即触发后台任务，但不返回 Promise，让弹窗立刻消失
        startOrganize(targetFolderId, targetFolderName)
      }
    })
  }

  const startOrganize = async (targetFolderId: string | null, targetFolderName: string) => {
    isOrganizing.value = true
    message.info(`AI 整理任务已启动 [${targetFolderName}]，详情见控制台`, { duration: 5000 })
    
    try {
      const response = await fetch('/api/bookmarks/ai-auto-organize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_id: targetFolderId })
      })

      if (!response.ok) throw new Error('网络请求失败')
      if (!response.body) throw new Error('未收到后台响应')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      console.log(`--- 🤖 AI 书签整理 [${targetFolderName}] 开始 ---`)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const statusText = line.replace('data: ', '').trim()
            console.log(`[AI] ${statusText}`)
          }
        }
      }

      console.log('--- ✅ AI 书签整理全部完成 ---')
      message.success('AI 整理已全部完成！')
      
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