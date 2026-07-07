<script lang="ts">
  import { editor, uploadFile } from '../editor.svelte'

  let hot = $state(false)
  let inputEl = $state<HTMLInputElement>()

  function pick(files: FileList | null | undefined) {
    if (files && files[0]) uploadFile(files[0])
  }
  function onDrop(e: DragEvent) {
    e.preventDefault()
    hot = false
    pick(e.dataTransfer?.files)
  }
</script>

<button
  class="dz"
  class:hot
  class:busy={editor.uploading}
  onclick={() => inputEl?.click()}
  ondragover={(e) => {
    e.preventDefault()
    hot = true
  }}
  ondragleave={() => (hot = false)}
  ondrop={onDrop}
>
  <input
    bind:this={inputEl}
    type="file"
    accept=".pdf,.png,.jpg,.jpeg,.bmp,.tif,.tiff,image/*,application/pdf"
    hidden
    onchange={(e) => pick(e.currentTarget.files)}
  />
  <span class="dz-icon" aria-hidden="true">
    {#if editor.uploading}
      <span class="spinner"></span>
    {:else}
      <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.6">
        <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke-linecap="round" stroke-linejoin="round" />
        <path d="M4 15v3a2 2 0 002 2h12a2 2 0 002-2v-3" stroke-linecap="round" />
      </svg>
    {/if}
  </span>
  <span class="dz-copy">
    <span class="dz-title">{editor.uploading ? 'Reading label…' : 'Drop a label to begin'}</span>
    <span class="dz-sub">PDF or image · normalized to a 4×6 (<span class="mono">812×1218</span>) ZPL label</span>
  </span>
  <span class="dz-hint mono">or press ⌘V / Ctrl+V to paste a screenshot</span>
  {#if editor.error}<span class="dz-err">{editor.error}</span>{/if}
</button>

<style>
  .dz {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-4);
    width: min(560px, 100%);
    padding: var(--sp-12) var(--sp-6);
    border: 1.5px dashed var(--line-strong);
    border-radius: var(--r-lg);
    background: var(--surface);
    color: var(--ink);
    text-align: center;
    cursor: pointer;
    transition:
      border-color var(--dur) var(--ease-out),
      background var(--dur) var(--ease-out);
  }
  .dz:hover,
  .dz.hot {
    border-color: var(--primary);
    background: var(--surface-2);
  }
  .dz.busy {
    cursor: progress;
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
  .dz-copy {
    display: flex;
    flex-direction: column;
    gap: var(--sp-1);
  }
  .dz-title {
    font-size: var(--fs-lg);
    font-weight: 600;
  }
  .dz-sub {
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
  .dz-err {
    color: var(--err);
    font-size: var(--fs-sm);
  }
  .spinner {
    width: 26px;
    height: 26px;
    border: 3px solid var(--line);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
