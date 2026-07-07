// Shared reactive editor state + API orchestration. Components stay presentational.

import { api, type ProfileInfo, type RenderParams, type UploadResult } from './api'

export type CropMode = 'profile' | 'auto' | 'manual' | 'none'

export const editor = $state({
  session: null as UploadResult | null,
  page: 0,
  profile: 'generic_4x6',
  cropMode: 'profile' as CropMode,
  rotate: 0,
  threshold: 128,
  crop: [0.1, 0.1, 0.9, 0.9] as number[],
  profiles: [] as ProfileInfo[],
  previewUrl: '',
  zplBytes: 0,
  rendering: false,
  uploading: false,
  printing: false,
  error: null as string | null,
})

export function sourceUrl(): string {
  return editor.session ? api.sourceUrl(editor.session.id, editor.page) : ''
}

export function renderParams(): RenderParams {
  return {
    id: editor.session!.id,
    page: editor.page,
    profile: editor.profile,
    rotate: editor.rotate,
    threshold: editor.threshold,
    crop_mode: editor.cropMode,
    crop: editor.cropMode === 'manual' ? editor.crop : null,
  }
}

export async function loadProfiles(): Promise<void> {
  try {
    editor.profiles = await api.profiles()
  } catch {
    /* status pill surfaces printer problems; profiles rarely fail */
  }
}

export async function uploadFile(file: File): Promise<void> {
  editor.uploading = true
  editor.error = null
  try {
    const res = await api.upload(file)
    editor.session = res
    editor.page = 0
    editor.profile = res.suggested_profile
    editor.cropMode = 'profile'
    editor.rotate = 0
    editor.threshold = 128
    await renderNow()
  } catch (e) {
    editor.error = e instanceof Error ? e.message : String(e)
  } finally {
    editor.uploading = false
  }
}

let renderTimer: ReturnType<typeof setTimeout> | undefined
export function scheduleRender(): void {
  clearTimeout(renderTimer)
  renderTimer = setTimeout(renderNow, 160)
}

export async function renderNow(): Promise<void> {
  if (!editor.session) return
  editor.rendering = true
  editor.error = null
  try {
    const { blob, zplBytes } = await api.render(renderParams())
    if (editor.previewUrl) URL.revokeObjectURL(editor.previewUrl)
    editor.previewUrl = URL.createObjectURL(blob)
    editor.zplBytes = zplBytes
  } catch (e) {
    editor.error = e instanceof Error ? e.message : String(e)
  } finally {
    editor.rendering = false
  }
}

export function setPage(page: number): void {
  if (!editor.session) return
  const clamped = Math.min(editor.session.pages - 1, Math.max(0, page))
  if (clamped !== editor.page) {
    editor.page = clamped
    renderNow()
  }
}

export async function printLabel(): Promise<{ ok: boolean; detail: string }> {
  if (!editor.session) return { ok: false, detail: 'No label loaded.' }
  editor.printing = true
  try {
    const res = await api.print(renderParams())
    return { ok: true, detail: res.detail }
  } catch (e) {
    return { ok: false, detail: e instanceof Error ? e.message : String(e) }
  } finally {
    editor.printing = false
  }
}

export function clearSession(): void {
  if (editor.previewUrl) URL.revokeObjectURL(editor.previewUrl)
  editor.session = null
  editor.previewUrl = ''
  editor.error = null
}
