import request from '@/utils/request'

export const aiApi = {
  // 获取配置
  getConfig() {
    return request({
      url: '/api/ai/config',
      method: 'get'
    })
  },
  
  // 保存配置
  saveConfig(data: { provider: string, api_key: string, base_url: string, model: string }) {
    return request({
      url: '/api/ai/config',
      method: 'post',
      data
    })
  },
  
  // 聊天接口 (流式通常通过 fetch 处理，这里仅保留非流式或作为占位)
  chat(messages: any[]) {
    return request({
      url: '/api/ai/chat',
      method: 'post',
      data: { messages }
    })
  }
}
