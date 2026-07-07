<script lang="ts">
  import { api } from '../api'
  import { editor, loadProfiles, scheduleRender } from '../editor.svelte'
  import { toast } from '../toast.svelte'
  import Button from './Button.svelte'

  let dialog = $state<HTMLDialogElement>()
  let name = $state('')
  let saving = $state(false)

  export function open() {
    name = ''
    dialog?.showModal()
  }

  async function save(e: SubmitEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    saving = true
    try {
      await api.saveProfile({
        name: trimmed,
        description: `Trained from ${editor.session?.name ?? 'upload'}`,
        page_type: 'letter',
        rotate: editor.rotate,
        threshold: editor.threshold,
        crop: editor.crop,
      })
      await loadProfiles()
      editor.profile = trimmed
      editor.cropMode = 'profile'
      scheduleRender()
      toast(`Saved profile “${trimmed}”`, 'ok')
      dialog?.close()
    } catch (err) {
      toast('Save failed: ' + (err instanceof Error ? err.message : String(err)), 'err')
    } finally {
      saving = false
    }
  }
</script>

<dialog bind:this={dialog} class="dlg" onclose={() => (saving = false)}>
  <form onsubmit={save}>
    <h2>Save crop as profile</h2>
    <p class="lede">
      Saves the current crop, rotation, and threshold as a reusable preset. It auto-applies
      to the next label from this layout.
    </p>
    <label class="fld">
      <span>Profile name</span>
      <!-- svelte-ignore a11y_autofocus -->
      <input bind:value={name} placeholder="e.g. ups_returns" autofocus spellcheck="false" />
    </label>
    <div class="params mono">
      crop [{editor.crop.map((v) => v.toFixed(2)).join(', ')}] · rot {editor.rotate}° · thr {editor.threshold}
    </div>
    <div class="row">
      <Button variant="ghost" onclick={() => dialog?.close()}>Cancel</Button>
      <Button variant="primary" type="submit" loading={saving} disabled={!name.trim()}>Save profile</Button>
    </div>
  </form>
</dialog>

<style>
  .dlg {
    width: min(420px, calc(100vw - 2rem));
    padding: 0;
    border: 1px solid var(--line);
    border-radius: var(--r-lg);
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow-pop);
  }
  .dlg::backdrop {
    background: oklch(0 0 0 / 0.5);
    backdrop-filter: blur(2px);
  }
  form {
    display: flex;
    flex-direction: column;
    gap: var(--sp-4);
    padding: var(--sp-6);
  }
  h2 {
    font-size: var(--fs-lg);
  }
  .lede {
    margin: 0;
    color: var(--ink-muted);
    font-size: var(--fs-sm);
  }
  .fld {
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--ink-muted);
  }
  .fld input {
    min-height: var(--tap);
    padding: 0 var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-base);
    font-weight: 400;
  }
  .fld input:focus-visible {
    border-color: var(--focus);
  }
  .params {
    font-size: var(--fs-xs);
    color: var(--ink-faint);
    padding: var(--sp-2) var(--sp-3);
    background: var(--surface-2);
    border-radius: var(--r-sm);
  }
  .row {
    display: flex;
    justify-content: flex-end;
    gap: var(--sp-2);
  }
</style>
