/**
 * 统一管理系统事件名、通知类型等字符串
 */
export const NOTIFICATION_EVENTS = [
  { label: '所有事件 (*)', value: '*' },
  { label: '备份成功 (backup.success)', value: 'backup.success' },
  { label: '备份失败 (backup.failed)', value: 'backup.failed' },
  { label: '登录提醒 (auth.login)', value: 'auth.login' },
  { label: '标签匹配 (autotag.match)', value: 'autotag.match' },
  { label: '标签任务完成 (autotag.task_done)', value: 'autotag.task_done' },
  { label: '容器操作 (docker.container_action)', value: 'docker.container_action' },
  { label: '主机维护 (docker.host_action)', value: 'docker.host_action' },
  { label: '系统告警 (system.alert)', value: 'system.alert' }
]

export const MEDIA_TYPES = {
  MOVIE: 'Movie',
  SERIES: 'Series',
  SEASON: 'Season',
  EPISODE: 'Episode'
}
