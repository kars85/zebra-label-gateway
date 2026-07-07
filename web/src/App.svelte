<script lang="ts">
  import { editor, loadProfiles, uploadFile } from './lib/editor.svelte'
  import DropZone from './lib/components/DropZone.svelte'
  import Editor from './lib/components/Editor.svelte'
  import StatusPill from './lib/components/StatusPill.svelte'
  import Toaster from './lib/components/Toaster.svelte'

  let theme = $state<'dark' | 'light' | null>(null)

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
    // Wired to the history panel in the next iteration.
  }

  $effect(() => {
    const saved = localStorage.getItem('zlg-theme')
    if (saved === 'light' || saved === 'dark') {
      theme = saved
      document.documentElement.setAttribute('data-theme', saved)
    }
    loadProfiles()
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
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
    <StatusPill />
  </header>

  <main class="main" class:centered={!editor.session}>
    {#if editor.session}
      <Editor {onHistoryChanged} />
    {:else}
      <DropZone />
    {/if}
  </main>
</div>

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
  .main.centered {
    display: grid;
    place-items: center;
  }
</style>
