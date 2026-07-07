<script lang="ts">
  import { api } from '../api'
  import { toast } from '../toast.svelte'
  import Button from './Button.svelte'

  interface Props {
    onSaved?: () => void
  }
  let { onSaved }: Props = $props()

  let dialog = $state<HTMLDialogElement>()
  let host = $state('')
  let port = $state(9100)
  let envLocked = $state(false)
  let saving = $state(false)

  export async function open() {
    try {
      const s = await api.settings()
      host = s.printer_host
      port = s.printer_port
      envLocked = s.env_locked
    } catch {
      /* leave defaults */
    }
    dialog?.showModal()
  }

  async function save(e: SubmitEvent) {
    e.preventDefault()
    saving = true
    try {
      await api.saveSettings({ printer_host: host.trim(), printer_port: Number(port) })
      toast('Settings saved', 'ok')
      onSaved?.()
      dialog?.close()
    } catch (err) {
      toast('Save failed: ' + (err instanceof Error ? err.message : String(err)), 'err')
    } finally {
      saving = false
    }
  }
</script>

<dialog bind:this={dialog} class="dlg">
  <form onsubmit={save}>
    <div class="head">
      <h2>Settings</h2>
      <button type="button" class="x" onclick={() => dialog?.close()} aria-label="Close">×</button>
    </div>

    <div class="body">
      <fieldset disabled={envLocked}>
        <legend>Printer</legend>
        <div class="grid">
          <label class="fld host">
            <span>Host / IP</span>
            <input bind:value={host} placeholder="10.10.100.107" spellcheck="false" class="mono" />
          </label>
          <label class="fld">
            <span>Port</span>
            <input type="number" bind:value={port} min="1" max="65535" class="mono" />
          </label>
        </div>
      </fieldset>
      {#if envLocked}
        <p class="note">The printer address is set by the container's environment (ZLG_PRINTER_HOST) and can't be changed here.</p>
      {:else}
        <p class="note">Raw TCP (ZPL) — usually port 9100. Test the connection from the status pill after saving.</p>
      {/if}
    </div>

    <div class="foot">
      <Button variant="ghost" onclick={() => dialog?.close()}>Close</Button>
      <Button variant="primary" type="submit" loading={saving} disabled={envLocked}>Save</Button>
    </div>
  </form>
</dialog>

<style>
  .dlg {
    width: min(460px, calc(100vw - 2rem));
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
    padding: var(--sp-5);
  }
  fieldset {
    margin: 0;
    padding: 0;
    border: none;
  }
  fieldset:disabled {
    opacity: 0.55;
  }
  legend {
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--ink-muted);
    padding: 0;
    margin-bottom: var(--sp-2);
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 90px;
    gap: var(--sp-3);
  }
  .fld {
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    font-size: var(--fs-xs);
    color: var(--ink-faint);
  }
  .fld input {
    min-height: var(--tap);
    padding: 0 var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-base);
  }
  .note {
    margin: var(--sp-4) 0 0;
    font-size: var(--fs-xs);
    color: var(--ink-faint);
  }
  .foot {
    display: flex;
    justify-content: flex-end;
    gap: var(--sp-2);
    padding: var(--sp-4) var(--sp-5);
    border-top: 1px solid var(--line);
  }
</style>
