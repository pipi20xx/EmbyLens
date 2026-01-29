import { h, Component } from 'vue'
import { NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  DashboardOutlined as DashboardIcon,
  AutoDeleteOutlined as DedupeIcon,
  SettingsOutlined as SettingIcon,
  TerminalOutlined as ConsoleIcon,
  PaletteOutlined as ThemeIcon,
  CategoryOutlined as CategoryIcon,
  LayersOutlined as CleanupIcon,
  LockOpenOutlined as LockIcon,
  CameraOutlined as LensIcon,
  SearchOutlined as SearchIcon,
  MyLocationOutlined as TargetIcon,
  YoutubeSearchedForOutlined as DeepSearchIcon,
  ScienceOutlined as LabIcon,
  ContactPageOutlined as ActorLabIcon,
  PeopleAltOutlined as ActorIcon,
  SyncAltOutlined as WebhookIcon,
  StorageOutlined as PostgresIcon,
  BackupOutlined as BackupIcon,
  CloudUploadOutlined as BuildIcon,
  NotificationsOutlined as NotificationIcon,
  AdminPanelSettingsOutlined as SecurityIcon,
  PersonOutlined as ProfileIcon
} from '@vicons/material'

// 自定义 Docker 图标组件
export const DockerIcon = {
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, [
      h('path', { d: 'M13.983 11.078h2.119c.102 0 .186-.085.186-.188V8.771c0-.103-.084-.188-.186-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM11.266 11.078h2.119c.102 0 .187-.085.187-.188V8.771c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM13.983 8.199h2.119c.102 0 .186-.084.186-.187V5.892c0-.103-.084-.188-.186-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM11.266 8.199h2.119c.102 0 .187-.084.187-.187V5.892c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM8.547 11.078h2.119c.103 0 .188-.085.188-.188V8.771c0-.103-.085-.188-.188-.188H8.547c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM11.266 5.321h2.119c.102 0 .187-.085.187-.188V3.014c0-.103-.085-.188-.187-.188h-2.119c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM8.547 8.199h2.119c.103 0 .188-.084.188-.187V5.892c0-.103-.085-.188-.188-.188H8.547c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM5.829 11.078h2.119c.103 0 .188-.085.188-.188V8.771c0-.103-.085-.188-.188-.188H5.829c-.103 0-.188.085-.188.188v2.119c0 .103.085.188.188.188zM16.7 8.199h2.119c.103 0 .188-.084.188-.187V5.892c0-.103-.085-.188-.188-.188H16.7c-.103 0-.188.085-.188.188v2.119c0 .103.085.187.188.187zM22.447 8.059c-1.022 0-2.564.399-3.441 1.435-.19.228-.338.478-.44.733H.683c-.047 0-.083.012-.11.037-.033.025-.05.062-.05.111v.592c0 .19.156.344.349.344l.181.011c.113.666.437 1.298.93 1.802 1.64 1.677 4.531 1.677 6.173 0 1.282-1.313 1.605-3.011 1.314-4.381h1.02c.02.011.039.024.058.042l.023.025a5.75 5.75 0 0 0 .773 1.106c.901.927 2.121 1.391 3.341 1.391 1.22 0 2.441-.464 3.341-1.391.431-.444.748-.96.953-1.523h4.089c.196 0 .355-.158.355-.354v-.711c0-.196-.159-.354-.355-.354z' })
    ])
  }
}

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

// 原始扁平化菜单项定义（用于引用和基础数据）
export const allMenuItems: MenuOption[] = [
  { label: '管理仪表盘', key: 'DashboardView', icon: renderIcon(DashboardIcon) },
  { label: '站点导航页', key: 'SiteNavView', icon: renderIcon(LensIcon) },
  
  { label: '重复项清理', key: 'DedupeView', icon: renderIcon(DedupeIcon) },
  { label: '类型映射管理', key: 'TypeManagerView', icon: renderIcon(CategoryIcon) },
  { label: '媒体净化清理', key: 'CleanupToolsView', icon: renderIcon(CleanupIcon) },
  { label: '元数据锁定器', key: 'LockManagerView', icon: renderIcon(LockIcon) },
  { label: '自动标签助手', key: 'AutoTagsView', icon: renderIcon(CategoryIcon) },
  
  { label: '项目元数据查询', key: 'EmbyItemQueryView', icon: renderIcon(SearchIcon) },
  { label: '剧集 TMDB 反查', key: 'TmdbReverseLookupView', icon: renderIcon(TargetIcon) },
  { label: 'TMDB ID 深度搜索', key: 'TmdbIdSearchView', icon: renderIcon(DeepSearchIcon) },
  
  { label: 'TMDB 实验中心', key: 'TmdbLabView', icon: renderIcon(LabIcon) },
  { label: 'Bangumi 实验室', key: 'BangumiLabView', icon: renderIcon(LabIcon) },
  { label: 'TMDB 演员实验室', key: 'ActorLabView', icon: renderIcon(ActorLabIcon) },
  { label: '演员信息维护', key: 'ActorManagerView', icon: renderIcon(ActorIcon) },
  
  { label: '终端管理', key: 'TerminalManagerView', icon: renderIcon(ConsoleIcon) },
  { label: 'Docker 容器管理', key: 'DockerManagerView', icon: renderIcon(DockerIcon) },
  { label: '镜像构建与推送', key: 'ImageBuilderView', icon: renderIcon(BuildIcon) },
  { label: 'PostgreSQL 管理', key: 'PostgresManagerView', icon: renderIcon(PostgresIcon) },
  { label: '数据备份管理', key: 'BackupManagerView', icon: renderIcon(BackupIcon) },
  
  { label: 'Webhook 接收器', key: 'WebhookReceiverView', icon: renderIcon(WebhookIcon) },
  { label: '通知消息中心', key: 'NotificationManagerView', icon: renderIcon(NotificationIcon) },
  { label: '账号安全管理', key: 'AccountManagerView', icon: renderIcon(ProfileIcon) },
  { label: '外部控制体系', key: 'ExternalControlView', icon: renderIcon(SecurityIcon) },
]

// 保持对原有 menuOptions 的兼容（为了不破坏现有的 store 逻辑）
export const menuOptions = allMenuItems

// 侧边栏分组定义
export const groupedMenuOptions = [
  {
    type: 'group',
    label: '概览控制',
    key: 'group-overview',
    children: [
      allMenuItems.find(i => i.key === 'DashboardView'),
      allMenuItems.find(i => i.key === 'SiteNavView'),
    ]
  },
  {
    type: 'group',
    label: '媒体工具',
    key: 'group-media',
    children: [
      allMenuItems.find(i => i.key === 'DedupeView'),
      allMenuItems.find(i => i.key === 'TypeManagerView'),
      allMenuItems.find(i => i.key === 'CleanupToolsView'),
      allMenuItems.find(i => i.key === 'LockManagerView'),
      allMenuItems.find(i => i.key === 'AutoTagsView'),
    ]
  },
  {
    type: 'group',
    label: '查询探索',
    key: 'group-search',
    children: [
      allMenuItems.find(i => i.key === 'EmbyItemQueryView'),
      allMenuItems.find(i => i.key === 'TmdbReverseLookupView'),
      allMenuItems.find(i => i.key === 'TmdbIdSearchView'),
    ]
  },
  {
    type: 'group',
    label: '实验室',
    key: 'group-labs',
    children: [
      allMenuItems.find(i => i.key === 'TmdbLabView'),
      allMenuItems.find(i => i.key === 'BangumiLabView'),
      allMenuItems.find(i => i.key === 'ActorLabView'),
      allMenuItems.find(i => i.key === 'ActorManagerView'),
    ]
  },
  {
    type: 'group',
    label: '系统维护',
    key: 'group-system',
    children: [
      allMenuItems.find(i => i.key === 'TerminalManagerView'),
      allMenuItems.find(i => i.key === 'DockerManagerView'),
      allMenuItems.find(i => i.key === 'ImageBuilderView'),
      allMenuItems.find(i => i.key === 'PostgresManagerView'),
      allMenuItems.find(i => i.key === 'BackupManagerView'),
    ]
  },
  {
    type: 'group',
    label: '配置中心',
    key: 'group-config',
    children: [
      allMenuItems.find(i => i.key === 'WebhookReceiverView'),
      allMenuItems.find(i => i.key === 'NotificationManagerView'),
      allMenuItems.find(i => i.key === 'AccountManagerView'),
      allMenuItems.find(i => i.key === 'ExternalControlView'),
    ]
  }
]

export { SettingIcon, ConsoleIcon, ThemeIcon }
