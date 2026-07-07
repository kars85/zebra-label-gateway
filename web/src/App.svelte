<script lang="ts">
  import StatusPill from './lib/components/StatusPill.svelte'

  let theme = $state<'dark' | 'light' | null>(null)

  function toggleTheme() {
    const current = theme ?? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark')
    theme = current === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('zlg-theme', theme)
  }

  $effect(() => {
    const saved = localStorage.getItem('zlg-theme')
    if (saved === 'light' || saved === 'dark') {
      theme = saved
      document.documentElement.setAttribute('data-theme', saved)
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
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke-linecap="round" />
      </svg>
    </button>
    <StatusPill />
  </header>

  <main class="stage">
    <div class="dropzone">
      <div class="dz-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
          <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M4 15v3a2 2 0 002 2h12a2 2 0 002-2v-3" stroke-linecap="round" />
        </svg>
      </div>
      <div class="dz-copy">
        <p class="dz-title">Drop a label to begin</p>
        <p class="dz-sub">PDF or image · normalized to a 4×6 (<span class="mono">812×1218</span>) ZPL label</p>
      </div>
      <div class="dz-hint mono">or press ⌘V to paste a screenshot</div>
    </div>
  </main>
</div>

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
    transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
  }
  .icon-btn:hover {
    color: var(--ink);
    border-color: var(--line-strong);
  }

  .stage {
    flex: 1;
    display: grid;
    place-items: center;
    padding: var(--sp-6);
  }
  .dropzone {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-4);
    width: min(560px, 100%);
    padding: var(--sp-12) var(--sp-6);
    border: 1.5px dashed var(--line-strong);
    border-radius: var(--r-lg);
    background: var(--surface);
    text-align: center;
    transition: border-color var(--dur) var(--ease-out), background var(--dur) var(--ease-out);
  }
  .dropzone:hover {
    border-color: var(--primary);
    background: var(--surface-2);
  }
  .dz-icon {
    display: grid;
    place-items: center;
    width: 64px;
    height: 64px;
    border-radius: var(--r-full);
    background: var(--surface-2);
    color: var(--ink-muted);
  }
  .dz-title {
    margin: 0;
    font-size: var(--fs-lg);
    font-weight: 600;
  }
  .dz-sub {
    margin: var(--sp-1) 0 0;
    color: var(--ink-muted);
    font-size: var(--fs-sm);
  }
  .dz-hint {
    font-size: var(--fs-xs);
    color: var(--ink-faint);
    padding: var(--sp-1) var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-full);
  }
</style>
