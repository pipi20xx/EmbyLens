import { ref, h, defineComponent, onMounted } from 'vue'
import { useMessage, useDialog, NDynamicTags, NAlert, NButton, NSpace, NDivider } from 'naive-ui'
import axios from 'axios'

// 1. 系统硬编码的默认分类（用于恢复默认功能）
const DEFAULT_CATEGORIES = [
  "媒体服务器", "动漫二次元", "游戏娱乐", "技术开发", 
  "实用工具", "资源下载", "社交资讯", "购物生活", "知识学习"
]

// 2. 抽离出一个真正的 Vue 组件，确保响应式万无一失
const AIConfigEditor = defineComponent({
  props: ['targetFolderName', 'categories'],
  emits: ['update:categories'],
  setup(props, { emit }) {
    const handleRestore = () => {
      emit('update:categories', [...DEFAULT_CATEGORIES])
    }

    return () => h('div', { style: 'display: flex; flex-direction: column; gap: 16px;' }, [
      h(NAlert, { title: '范围确认', type: 'warning', bordered: false }, {
        default: () => [
          h('div', null, `整理目标：${props.targetFolderName}`),
          h('div', { style: 'font-size: 12px; margin-top: 4px; opacity: 0.7;' }, '💡 提示：你可以通过左侧目录树选中特定文件夹进行局部处理。')
        ]
      }),
      h('div', null, [
        h('div', { style: 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;' }, [
          h('span', { style: 'font-weight: bold;' }, '分类标准预设：'),
          h(NButton, { size: 'tiny', quaternary: true, type: 'primary', onClick: handleRestore }, { default: () => '恢复系统默认' })
        ]),
        h(NDynamicTags, {
          value: props.categories,
          'onUpdate:value': (val: string[]) => emit('update:categories', val)
        }),
        h('p', { style: 'color: #999; font-size: 12px; margin-top: 10px;' }, 'AI 将严格按此列表归类（严禁自建）。请手动剔除不想要的分类。')
      ])
    ])
  }
})

export function useBookmarkAI(bookmarkApi: any, actions: any, state: any) {
  const message = useMessage()
  const dialog = useDialog()
  const isOrganizing = ref(false)

  const handleAIAnalyze = async () => {
    if (isOrganizing.value) return
    
    // 1. 自动从 config.json 加载
    let currentCategories = ref<string[]>([])
    try {
      const res = await axios.get('/api/system/config')
      const raw = res.data.ai_bookmark_categories
      // 如果后端没数据，则使用前端默认值
      currentCategories.value = (Array.isArray(raw) && raw.length > 0) ? raw : [...DEFAULT_CATEGORIES]
    } catch (e) {
      currentCategories.value = [...DEFAULT_CATEGORIES]
    }

    const selectedFolderId = state.selectedKeys.value[0]
    const targetFolderId = (selectedFolderId === 'root' || !selectedFolderId) ? null : selectedFolderId
    const targetFolderName = targetFolderId ? actions.findItemById(state.bookmarks.value, targetFolderId)?.title : '全部书签'

    // 2. 弹出窗口
    const d = dialog.info({
      title: 'AI 整理配置',
      style: 'width: 520px',
      content: () => h(AIConfigEditor, {
        targetFolderName,
        categories: currentCategories.value,
        'onUpdate:categories': (val: string[]) => { currentCategories.value = val }
      }),
      action: () => h(NSpace, { justify: 'end' }, {
        default: () => [
          h(NButton, { 
            quaternary: true,
            onClick: () => { d.destroy() } 
          }, { default: () => '取消' }),
          h(NButton, { 
            secondary: true, 
            type: 'info',
            onClick: async () => {
              await saveCategories(currentCategories.value)
              message.success('分类预设已保存至 config.json')
              d.destroy()
            }
          }, { default: () => '仅保存分类' }),
          h(NButton, { 
            type: 'primary',
            onClick: async () => {
              await saveCategories(currentCategories.value)
              d.destroy()
              startOrganize(targetFolderId, targetFolderName)
            }
          }, { default: () => '启动 AI 整理' })
        ]
      })
    })
  }

  const saveCategories = async (cats: string[]) => {
    try {
      await axios.post('/api/system/config', {
        configs: [{ key: 'ai_bookmark_categories', value: cats }]
      })
    } catch (e) {
      message.error('保存失败')
      throw e
    }
  }

  const startOrganize = async (targetFolderId: string | null, targetFolderName: string) => {
    isOrganizing.value = true
    message.info(`AI 整理任务已启动 [${targetFolderName}]`, { duration: 5000 })
    
    try {
      const response = await fetch('/api/bookmarks/ai-auto-organize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_id: targetFolderId })
      })

      if (!response.ok) throw new Error('网络请求失败')
      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      console.log(`--- 🤖 AI 书签整理 [${targetFolderName}] 开始 ---`)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        chunk.split('\n').forEach(line => {
          if (line.startsWith('data: ')) {
            console.log(`[AI] ${line.replace('data: ', '').trim()}`)
          }
        })
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
