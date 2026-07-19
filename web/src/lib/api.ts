// Typed client for the FastAPI backend. Same-origin; no base URL needed.

export interface PrinterStatus {
  ok: boolean
  printer: string
  report?: string
  flags?: Record<string, unknown>
  detail?: string
}

export interface ProfileInfo {
  name: string
  description: string
  rotate: number
  threshold: number
  crop: unknown
  page_type: string
}

export interface UploadResult {
  id: string
  kind: 'pdf' | 'image' | 'zpl'
  name: string
  width?: number
  height?: number
  pages: number
  source_url?: string
  zpl_bytes?: number
  suggested_profile: string
}

export interface HistoryEntry {
  id: string
  name: string
  profile: string
  page: number
  created: string
  zpl_bytes: number
  printed: boolean
  preview_url: string
}

export interface RenderParams {
  id: string
  page?: number
  profile: string
  rotate?: number | null
  threshold?: number | null
  crop?: number[] | string | null
  crop_mode?: 'profile' | 'auto' | 'manual' | 'none'
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  status: () => fetch('/api/status').then((r) => r.json() as Promise<PrinterStatus>),

  profiles: () => fetch('/api/profiles').then(json<ProfileInfo[]>),

  async upload(file: File): Promise<UploadResult> {
    const body = new FormData()
    body.append('file', file)
    return json<UploadResult>(await fetch('/api/upload', { method: 'POST', body }))
  },

  sourceUrl: (id: string, page: number) => `/api/source/${id}?page=${page}&t=${Date.now()}`,

  async render(params: RenderParams): Promise<{ blob: Blob; zplBytes: number }> {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `HTTP ${res.status}`)
    return { blob: await res.blob(), zplBytes: Number(res.headers.get('X-Zpl-Bytes') ?? 0) }
  },

  print: (params: RenderParams) =>
    fetch('/api/print', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    }).then(json<{ ok: boolean; detail: string; zpl_bytes: number }>),

  settings: () => fetch('/api/settings').then(json<{ printer_host: string; printer_port: number; env_locked: boolean }>),
  saveSettings: (spec: { printer_host?: string; printer_port?: number }) =>
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
    }).then(json<{ ok: boolean; printer_host: string; printer_port: number }>),

  history: () => fetch('/api/history').then(json<HistoryEntry[]>),
  reprint: (id: string) => fetch(`/api/history/${id}/reprint`, { method: 'POST' }).then(json<{ ok: boolean; detail: string }>),
  deleteHistory: (id: string) => fetch(`/api/history/${id}`, { method: 'DELETE' }).then(json<{ ok: boolean }>),

  saveProfile: (spec: {
    name: string
    description?: string
    page_type?: string
    rotate?: number
    threshold?: number
    crop?: number[] | string | null
  }) =>
    fetch('/api/profiles/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
    }).then(json<{ ok: boolean; name: string }>),
}

export function printerProblems(status: PrinterStatus | null): string[] {
  const flags = (status?.flags ?? {}) as Record<string, unknown>
  return ['paper_out', 'head_open', 'paused', 'ribbon_out'].filter((k) => flags[k])
}
