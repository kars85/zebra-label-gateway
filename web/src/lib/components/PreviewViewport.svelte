<script lang="ts">
  import { editor } from '../editor.svelte'

  let zoomed = $state(false)
  const kb = $derived(editor.zplBytes ? (editor.zplBytes / 1024).toFixed(1) + ' KB' : '')
</script>

<div class="pane">
  <header class="pane-head">
    <span class="pane-title">4×6 Preview</span>
    <span class="pane-meta mono">
      {#if editor.rendering}rendering…{:else if kb}ZPL {kb}{/if}
    </span>
  </header>

  <div class="viewport" class:zoom={zoomed}>
    {#if editor.previewUrl}
      <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
      <img
        src={editor.previewUrl}
        alt="Normalized 4×6 label preview"
        class:busy={editor.rendering}
        onclick={() => (zoomed = !zoomed)}
        title={zoomed ? 'Click to fit' : 'Click for actual size (100%)'}
      />
    {:else}
      <div class="ph"></div>
    {/if}
  </div>
  <p class="hint">Exactly what prints — click to inspect at 100%</p>
</div>

<style>
  .pane {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .pane-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: var(--sp-3);
  }
  .pane-title {
    font-size: var(--fs-sm);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--ink-muted);
  }
  .pane-meta {
    font-size: var(--fs-xs);
    color: var(--ink-faint);
  }

  .viewport {
    display: grid;
    place-items: center;
    flex: 1;
  }
  .viewport img {
    max-width: 100%;
    max-height: 62vh;
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: oklch(1 0 0);
    image-rendering: auto; /* high-quality downscale, never nearest-neighbor */
    cursor: zoom-in;
    box-shadow: var(--shadow-1);
    transition: opacity var(--dur) var(--ease-out);
  }
  .viewport img.busy {
    opacity: 0.45;
  }
  .viewport.zoom {
    overflow: auto;
    max-height: 66vh;
    place-items: start;
  }
  .viewport.zoom img {
    max-width: none;
    max-height: none;
    width: 812px;
    image-rendering: pixelated;
    cursor: zoom-out;
  }
  .ph {
    width: min(280px, 60%);
    aspect-ratio: 812 / 1218;
    border: 1px dashed var(--line);
    border-radius: var(--r-md);
    background: var(--surface);
  }
  .hint {
    margin: var(--sp-3) 0 0;
    font-size: var(--fs-xs);
    color: var(--ink-faint);
    text-align: center;
  }
</style>
