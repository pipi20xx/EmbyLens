export interface DockerHost {
  id: string
  name: string
  host: string
  port: number
  compose_scan_paths?: string
  [key: string]: any
}

export interface AutoUpdateSettings {
  enabled: boolean
  type: 'cron' | 'interval'
  value: string
}
