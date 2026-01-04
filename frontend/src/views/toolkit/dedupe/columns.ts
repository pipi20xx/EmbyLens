import { h, Component } from 'vue'
import { NText, NTag, NIcon, NSpace } from 'naive-ui'
import { 
  TvOutlined as SeriesIcon,
  FolderOutlined as SeasonIcon,
  MovieOutlined as MovieIcon,
  InsertDriveFileOutlined as EpisodeIcon 
} from '@vicons/material'

function renderIcon(icon: Component) {
  return h(NIcon, { style: 'vertical-align: -3px; margin-right: 4px;' }, { default: () => h(icon) })
}

export const getColumns = () => [
  { type: 'selection' },
  {
    title: '媒体名称 / 路径',
    key: 'name',
    width: 400,
    render(row: any) {
      let icon = MovieIcon
      let typeColor = 'default'
      let displayName = row.name

      // 根据类型分配图标和显示格式
      if (row.item_type === 'Series') { icon = SeriesIcon; typeColor = 'primary' }
      else if (row.item_type === 'Season') {
        icon = SeasonIcon
        const idx = row.raw_data?.IndexNumber
        displayName = `第 ${String(idx || 0).padStart(2, '0')} 季`
      }
      else if (row.item_type === 'Episode') {
        icon = EpisodeIcon
        const s = row.raw_data?.ParentIndexNumber
        const e = row.raw_data?.IndexNumber
        displayName = `S${String(s || 0).padStart(2, '0')}E${String(e || 0).padStart(2, '0')} - ${row.name}`
      }

      return h('div', { style: 'padding-left: 4px' }, [
        h(NSpace, { align: 'center', size: 'small' }, {
          default: () => [
            renderIcon(icon),
            h(NText, { 
              strong: row.item_type === 'Series' || row.item_type === 'Movie',
              type: row.is_duplicate ? 'warning' : 'default',
              style: row.item_type === 'Episode' ? 'font-size: 13px;' : 'font-size: 14px;'
            }, { default: () => displayName })
          ]
        }),
        h('div', { 
          style: 'font-size: 10px; opacity: 0.4; font-family: monospace; margin-top: 4px; padding-left: 24px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 500px;' 
        }, row.path)
      ])
    }
  },
  {
    title: '类型',
    key: 'item_type',
    width: 80,
    render(row: any) {
      const typeMap: any = { 'Movie': '电影', 'Series': '剧集', 'Season': '季', 'Episode': '集' }
      const colorMap: any = { 'Movie': 'success', 'Series': 'info', 'Season': 'warning', 'Episode': 'default' }
      return h(NTag, { 
        size: 'small', 
        bordered: false, 
        type: colorMap[row.item_type] || 'default' 
      }, { default: () => typeMap[row.item_type] || row.item_type })
    }
  },
  {
    title: '规格 / 编码 / 范围',
    key: 'specs',
    width: 250,
    render(row: any) {
      if (row.item_type === 'Series' || row.item_type === 'Season') return h(NText, { depth: 3 }, { default: () => '-' })
      
      return h(NSpace, { size: 'small' }, {
        default: () => [
          row.display_title !== 'N/A' ? h(NTag, { size: 'tiny', type: 'info', ghost: true }, { default: () => row.display_title }) : null,
          h(NText, { depth: 3, style: 'font-size: 11px' }, { default: () => row.video_codec }),
          row.video_range !== 'SDR' ? h(NTag, { size: 'tiny', type: 'error' }, { default: () => row.video_range }) : null
        ]
      })
    }
  },
  {
    title: 'Emby ID',
    key: 'id',
    width: 120,
    render(row: any) {
      return h(NText, { code: true, depth: 3, style: 'font-size: 11px' }, { default: () => row.id })
    }
  },
  {
    title: 'TMDB',
    key: 'tmdb_id',
    width: 100,
    render(row: any) {
      return h(NText, { depth: 3, style: 'font-size: 11px' }, { default: () => row.tmdb_id || '-' })
    }
  }
]
