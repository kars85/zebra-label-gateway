<script lang="ts">
  import { api, printerProblems, type PrinterStatus } from '../api'

  let dialog = $state<HTMLDialogElement>()
  let status = $state<PrinterStatus | null>(null)
  let loading = $state(false)

  const GUIDANCE: Record<string, string> = {
    paper_out: 'Load media, then hold FEED to recalibrate.',
    head_open: 'Close and latch the print head firmly.',
    paused: 'Press the pause button on the printer to resume.',
    ribbon_out: 'Install a ribbon — the printer is in thermal-transfer mode.',
  }

  export async function open() {
    dialog?.showModal()
    await load()
  }

  async function load() {
    loading = true
    try {
      status = await api.status()
    } catch {
      status = null
    }
    loading = false
  }

  const problems = $derived(printerProblems(status))
</script>

<dialog bind:this={dialog} class="dlg">
  <div class="head">
    <h2>Printer status</h2>
    <button class="x" onclick={() => dialog?.close()} aria-label="Close">×</button>
  </div>

  <div class="body">
    <div class="line">
      <span class="mono target">{status?.printer ?? '—'}</span>
      <span class="badge {!status || !status.ok ? 'err' : problems.length ? 'warn' : 'ok'}">
        {!status || !status.ok ? 'offline' : problems.length ? 'attention' : 'ready'}
      </span>
      <button class="refresh" onclick={load} disabled={loading}>{loading ? 'checking…' : 'Refresh'}</button>
    </div>

    {#if problems.length}
      <ul class="guidance">
        {#each problems as p (p)}
          <li><strong>{p.replace('_', ' ')}</strong> — {GUIDANCE[p] ?? 'Check the printer.'}</li>
        {/each}
      </ul>
    {/if}

    {#if status?.report}
      <pre class="report mono">{status.report}</pre>
    {:else if status && !status.ok}
      <p class="offline">No response from the printer. Check the network and address in Settings.</p>
    {/if}
  </div>
</dialog>

<style>
  .dlg {
    width: min(520px, calc(100vw - 2rem));
    padding: 0;
    border: 1px solid var(--line);
    border-radius: var(--r-lg);
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow-pop);
  }
  .dlg::backdrop {
    background: oklch(0 0 0 / 0.5);
  }
  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--sp-4) var(--sp-5);
    border-bottom: 1px solid var(--line);
  }
  h2 {
    font-size: var(--fs-md);
  }
  .x {
    width: 32px;
    height: 32px;
    border: none;
    background: none;
    color: var(--ink-muted);
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    border-radius: var(--r-sm);
  }
  .x:hover {
    background: var(--surface-2);
    color: var(--ink);
  }
  .body {
    display: flex;
    flex-direction: column;
    gap: var(--sp-4);
    padding: var(--sp-5);
  }
  .line {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
  }
  .target {
    font-size: var(--fs-base);
  }
  .badge {
    font-size: var(--fs-xs);
    padding: 2px var(--sp-2);
    border-radius: var(--r-full);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .badge.ok {
    background: var(--primary-quiet);
    color: var(--primary);
  }
  .badge.warn {
    background: var(--warn-quiet);
    color: var(--warn);
  }
  .badge.err {
    background: var(--err-quiet);
    color: var(--err);
  }
  .refresh {
    margin-left: auto;
    padding: var(--sp-1) var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-sm);
    cursor: pointer;
  }
  .guidance {
    margin: 0;
    padding-left: var(--sp-5);
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    font-size: var(--fs-sm);
    color: var(--warn);
  }
  .report {
    margin: 0;
    padding: var(--sp-3);
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    font-size: var(--fs-xs);
    color: var(--ink-muted);
    white-space: pre-wrap;
    overflow-x: auto;
  }
  .offline {
    margin: 0;
    color: var(--ink-muted);
    font-size: var(--fs-sm);
  }
</style>
