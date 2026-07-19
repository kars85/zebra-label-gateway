<script lang="ts">
  import { clearSession, editor, printLabel } from '../editor.svelte'
  import { toast } from '../toast.svelte'
  import AdjustPanel from './AdjustPanel.svelte'
  import Button from './Button.svelte'
  import CropStage from './CropStage.svelte'
  import PreviewViewport from './PreviewViewport.svelte'
  import ProfileSaveDialog from './ProfileSaveDialog.svelte'

  interface Props {
    onHistoryChanged: () => void
  }
  let { onHistoryChanged }: Props = $props()

  let saveDialog = $state<ReturnType<typeof ProfileSaveDialog>>()

  async function printRaw() {
    const res = await printLabel()
    toast(res.ok ? '✓ ' + res.detail : 'Print failed: ' + res.detail, res.ok ? 'ok' : 'err')
  }
</script>

<div class="editor">
  <div class="filebar">
    <span class="fname" title={editor.session?.name}>{editor.session?.name}</span>
    <button class="new" onclick={clearSession}>
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 5v14M5 12h14" stroke-linecap="round" />
      </svg>
      New label
    </button>
  </div>

  {#if editor.session?.kind === 'zpl'}
    <section class="raw-card">
      <h2>Raw ZPL ready</h2>
      <p class="mono">{editor.zplBytes.toLocaleString()} bytes</p>
      <p>No preview or adjustments are available. The ASCII ZPL is sent directly and is not saved to Recent labels.</p>
      <p class="warning">Only print ZPL files you trust.</p>
      <Button variant="primary" loading={editor.printing} onclick={printRaw}>Print raw ZPL</Button>
    </section>
  {:else}
    <div class="grid">
      <section class="col"><CropStage /></section>
      <section class="col adjust">
        <AdjustPanel onSaveProfile={() => saveDialog?.open()} onPrinted={onHistoryChanged} />
      </section>
      <section class="col"><PreviewViewport /></section>
    </div>
  {/if}
</div>

<ProfileSaveDialog bind:this={saveDialog} />

<style>
  .editor {
    display: flex;
    flex-direction: column;
    gap: var(--sp-4);
  }
  .raw-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-3);
    width: min(480px, 100%);
    margin: var(--sp-8) auto 0;
    padding: var(--sp-6);
    border: 1px solid var(--line);
    border-radius: var(--r-lg);
    background: var(--surface);
  }
  .raw-card h2,
  .raw-card p {
    margin: 0;
  }
  .raw-card p {
    color: var(--ink-muted);
  }
  .raw-card .warning {
    color: var(--err);
  }
  .filebar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--sp-3);
  }
  .fname {
    font-size: var(--fs-sm);
    color: var(--ink-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .new {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-2);
    padding: var(--sp-2) var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-sm);
    cursor: pointer;
    white-space: nowrap;
  }
  .new:hover {
    border-color: var(--line-strong);
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr 300px 1fr;
    gap: var(--sp-4);
    align-items: start;
  }
  .col {
    padding: var(--sp-4);
    border: 1px solid var(--line);
    border-radius: var(--r-lg);
    background: var(--surface);
  }
  .adjust {
    position: sticky;
    top: calc(var(--toolbar-h) + var(--sp-4));
  }

  @media (max-width: 1100px) {
    .grid {
      grid-template-columns: 1fr 1fr;
    }
    .adjust {
      grid-column: 1 / -1;
      grid-row: 1;
      position: static;
    }
  }
  @media (max-width: 720px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
