<script lang="ts">
  import { editor, loadProfiles, printLabel, setPage, uploadFile } from './lib/editor.svelte'
  import { toast } from './lib/toast.svelte'
  import DropZone from './lib/components/DropZone.svelte'
  import Editor from './lib/components/Editor.svelte'
  import HistoryPanel from './lib/components/HistoryPanel.svelte'
  import SettingsDialog from './lib/components/SettingsDialog.svelte'
  import StatusDialog from './lib/components/StatusDialog.svelte'
  import StatusPill from './lib/components/StatusPill.svelte'
  import Toaster from './lib/components/Toaster.svelte'

  let theme = $state<'dark' | 'light' | null>(null)
  let statusPill = $state<ReturnType<typeof StatusPill>>()
  let statusDialog = $state<ReturnType<typeof StatusDialog>>()
  let settingsDialog = $state<ReturnType<typeof SettingsDialog>>()
  let historyPanel = $state<ReturnType<typeof HistoryPanel>>()

  function toggleTheme() {
    const current = theme ?? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')
    theme = current === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('zlg-theme', theme)
  }

  function onPaste(e: ClipboardEvent) {
    const file = Array.from(e.clipboardData?.items ?? [])
      .find((i) => i.type.startsWith('image/') || i.type === 'application/pdf')
      ?.getAsFile()
    if (file) uploadFile(file)
  }

  function onHistoryChanged() {
    historyPanel?.refresh()
  }

  async function doPrint() {
    if (!editor.session || editor.printing) return
    const res = await printLabel()
    toast(res.ok ? '✓ ' + res.detail : 'Print failed: ' + res.detail, res.ok ? 'ok' : 'err')
    if (res.ok) onHistoryChanged()
  }

  function onKeydown(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'p') {
      e.preventDefault()
      doPrint()
      return
    }
    const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)
    if (typing || !editor.session || e.metaKey || e.ctrlKey) return
    if (e.key === '[') setPage(editor.page - 1)
    else if (e.key === ']') setPage(editor.page + 1)
  }

  $effect(() => {
    const saved = localStorage.getItem('zlg-theme')
    if (saved === 'light' || saved === 'dark') {
      theme = saved
      document.documentElement.setAttribute('data-theme', saved)
    }
    loadProfiles()
    window.addEventListener('paste', onPaste)
    window.addEventListener('keydown', onKeydown)
    return () => {
      window.removeEventListener('paste', onPaste)
      window.removeEventListener('keydown', onKeydown)
    }
  })
</script>

<div class="app">
  <header class="toolbar">
    <div class="brand">
      <span class="glyph" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="13" rx="1.5" />
          <path d="M6 8v5M9 8v5M12 8v5M15 8v5M18 8v5" />
          <path d="M7 20h10" stroke-linecap="round" />
        </svg>
      </span>
      <div class="wordmark">
        <span class="name">Label Gateway</span>
        <span class="sub mono">ZD421 · 4×6 · 203dpi</span>
      </div>
    </div>

    <div class="spacer"></div>

    <button class="icon-btn" onclick={toggleTheme} title="Toggle theme" aria-label="Toggle light or dark theme">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="4" />
        <path
          d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
          stroke-linecap="round"
        />
      </svg>
    </button>
    <button class="icon-btn" onclick={() => settingsDialog?.open()} title="Settings" aria-label="Settings">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9c.2.61.76 1.03 1.42 1.09H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z" />
      </svg>
    </button>
    <StatusPill bind:this={statusPill} onclick={() => statusDialog?.open()} />
  </header>

  <main class="main">
    {#if editor.session}
      <Editor {onHistoryChanged} />
    {:else}
      <div class="empty"><DropZone /></div>
    {/if}
    <HistoryPanel bind:this={historyPanel} />
  </main>

  {#if editor.session}
    <div class="mobile-print">
      <button onclick={doPrint} disabled={editor.printing}>
        {editor.printing ? 'Printing…' : 'Print label'}
      </button>
    </div>
  {/if}
</div>

<StatusDialog bind:this={statusDialog} />
<SettingsDialog bind:this={settingsDialog} onSaved={() => statusPill?.refresh()} />
<Toaster />

<style>
  .app {
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
  }
  .toolbar {
    position: sticky;
    top: 0;
    z-index: var(--z-sticky);
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    height: var(--toolbar-h);
    padding: 0 var(--sp-4);
    padding-top: env(safe-area-inset-top);
    border-bottom: 1px solid var(--line);
    background: color-mix(in oklch, var(--bg) 88%, transparent);
    backdrop-filter: blur(8px);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
  }
  .glyph {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border-radius: var(--r-md);
    background: var(--primary-quiet);
    color: var(--primary);
  }
  .wordmark {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
  }
  .name {
    font-weight: 650;
    font-size: var(--fs-base);
    letter-spacing: -0.01em;
  }
  .sub {
    font-size: 0.6875rem;
    color: var(--ink-faint);
  }
  .spacer {
    flex: 1;
  }
  .icon-btn {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink-muted);
    cursor: pointer;
    transition:
      color var(--dur-fast) var(--ease-out),
      border-color var(--dur-fast) var(--ease-out);
  }
  .icon-btn:hover {
    color: var(--ink);
    border-color: var(--line-strong);
  }

  .main {
    flex: 1;
    padding: var(--sp-5);
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
  }
  @media (max-width: 560px) {
    .toolbar {
      gap: var(--sp-2);
      padding: 0 var(--sp-3);
    }
    .sub {
      display: none;
    }
  }
  .empty {
    display: grid;
    place-items: center;
    min-height: 46vh;
  }

  /* Thumb-reachable sticky Print on phones; hidden where the panel is visible. */
  .mobile-print {
    display: none;
  }
  @media (max-width: 720px) {
    .mobile-print {
      display: block;
      position: fixed;
      inset: auto 0 0 0;
      z-index: var(--z-sticky);
      padding: var(--sp-3) var(--sp-4);
      padding-bottom: calc(var(--sp-3) + env(safe-area-inset-bottom));
      background: color-mix(in oklch, var(--bg) 90%, transparent);
      backdrop-filter: blur(8px);
      border-top: 1px solid var(--line);
    }
    .mobile-print button {
      width: 100%;
      min-height: var(--tap);
      border: 1px solid var(--primary);
      border-radius: var(--r-md);
      background: var(--primary);
      color: var(--on-primary);
      font-size: var(--fs-md);
      font-weight: 650;
      cursor: pointer;
    }
    .mobile-print button:disabled {
      opacity: 0.6;
    }
    .main {
      padding-bottom: 84px;
    }
  }
</style>
