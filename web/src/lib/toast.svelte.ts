// Minimal toast queue.

export interface Toast {
  id: number
  message: string
  kind: 'ok' | 'err' | 'info'
}

export const toasts = $state({ items: [] as Toast[] })

let counter = 0

export function toast(message: string, kind: Toast['kind'] = 'info'): void {
  const id = ++counter
  toasts.items = [...toasts.items, { id, message, kind }]
  setTimeout(() => dismiss(id), 3600)
}

export function dismiss(id: number): void {
  toasts.items = toasts.items.filter((t) => t.id !== id)
}
