<script lang="ts">
  import { editor, scheduleRender, setPage, sourceUrl } from '../editor.svelte'

  let imgEl = $state<HTMLImageElement>()
  let interaction: null | 'draw' | 'move' | 'resize' = null
  let corner = ''
  let startX = 0
  let startY = 0
  let startCrop: number[] = []

  const manual = $derived(editor.cropMode === 'manual')
  const src = $derived(sourceUrl())

  const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))

  function toFrac(e: PointerEvent): [number, number] {
    const r = imgEl!.getBoundingClientRect()
    return [clamp((e.clientX - r.left) / r.width, 0, 1), clamp((e.clientY - r.top) / r.height, 0, 1)]
  }

  function onPointerDown(e: PointerEvent) {
    if (!manual) return
    e.preventDefault()
    const target = e.target as HTMLElement
    ;[startX, startY] = toFrac(e)
    startCrop = editor.crop.slice()
    if (target.dataset.handle) {
      interaction = 'resize'
      corner = target.dataset.handle
    } else if (target.classList.contains('cropbox')) {
      interaction = 'move'
    } else {
      interaction = 'draw'
      editor.crop = [startX, startY, startX, startY]
    }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  function onPointerMove(e: PointerEvent) {
    if (!interaction) return
    const [fx, fy] = toFrac(e)
    let [l, t, r, b] = editor.crop
    if (interaction === 'draw') {
      l = Math.min(startX, fx)
      r = Math.max(startX, fx)
      t = Math.min(startY, fy)
      b = Math.max(startY, fy)
    } else if (interaction === 'move') {
      const w = startCrop[2] - startCrop[0]
      const h = startCrop[3] - startCrop[1]
      l = clamp(startCrop[0] + (fx - startX), 0, 1 - w)
      t = clamp(startCrop[1] + (fy - startY), 0, 1 - h)
      r = l + w
      b = t + h
    } else if (interaction === 'resize') {
      if (corner.includes('w')) l = Math.min(fx, r - 0.02)
      if (corner.includes('e')) r = Math.max(fx, l + 0.02)
      if (corner.includes('n')) t = Math.min(fy, b - 0.02)
      if (corner.includes('s')) b = Math.max(fy, t + 0.02)
    }
    editor.crop = [l, t, r, b]
  }

  function onPointerUp(e: PointerEvent) {
    if (!interaction) return
    interaction = null
    try {
      ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
    } catch {
      /* pointer already released */
    }
    scheduleRender()
  }

  function onKeydown(e: KeyboardEvent) {
    if (!manual) return
    const step = e.shiftKey ? 0.02 : 0.004
    let [l, t, r, b] = editor.crop
    const w = r - l
    const h = b - t
    switch (e.key) {
      case 'ArrowLeft': l = clamp(l - step, 0, 1 - w); r = l + w; break
      case 'ArrowRight': l = clamp(l + step, 0, 1 - w); r = l + w; break
      case 'ArrowUp': t = clamp(t - step, 0, 1 - h); b = t + h; break
      case 'ArrowDown': t = clamp(t + step, 0, 1 - h); b = t + h; break
      default: return
    }
    e.preventDefault()
    editor.crop = [l, t, r, b]
    scheduleRender()
  }

  const boxStyle = $derived(
    `left:${editor.crop[0] * 100}%;top:${editor.crop[1] * 100}%;` +
      `width:${(editor.crop[2] - editor.crop[0]) * 100}%;height:${(editor.crop[3] - editor.crop[1]) * 100}%`,
  )
</script>

<div class="pane">
  <header class="pane-head">
    <span class="pane-title">Source</span>
    <span class="pane-meta mono">{editor.session?.width}×{editor.session?.height}</span>
  </header>

  {#if (editor.session?.pages ?? 1) > 1}
    <div class="pagenav">
      <button onclick={() => setPage(editor.page - 1)} disabled={editor.page <= 0} aria-label="Previous page">‹</button>
      <span class="mono">Page {editor.page + 1} / {editor.session?.pages}</span>
      <button
        onclick={() => setPage(editor.page + 1)}
        disabled={editor.page >= (editor.session?.pages ?? 1) - 1}
        aria-label="Next page">›</button
      >
    </div>
  {/if}

  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="stage"
    class:manual
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    onpointerup={onPointerUp}
    onpointercancel={onPointerUp}
  >
    <img bind:this={imgEl} {src} alt="Source label" draggable="false" />
    {#if manual}
      <div
        class="cropbox"
        style={boxStyle}
        tabindex="0"
        role="slider"
        aria-label="Crop region — arrow keys to nudge"
        aria-valuenow={Math.round((editor.crop[2] - editor.crop[0]) * 100)}
        onkeydown={onKeydown}
      >
        <span class="handle" data-handle="nw"></span>
        <span class="handle" data-handle="ne"></span>
        <span class="handle" data-handle="sw"></span>
        <span class="handle" data-handle="se"></span>
      </div>
    {/if}
  </div>

  <p class="hint">
    {#if manual}Drag to frame the label · corners resize · arrow keys nudge{:else if editor.cropMode === 'auto'}Auto-cropping to the largest content block{:else if editor.cropMode === 'none'}Using the whole page{:else}Using the profile's crop setting{/if}
  </p>
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

  .pagenav {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    margin-bottom: var(--sp-3);
    font-size: var(--fs-sm);
  }
  .pagenav button {
    width: 30px;
    height: 30px;
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    background: var(--surface-2);
    color: var(--ink);
    cursor: pointer;
    font-size: var(--fs-md);
    line-height: 1;
  }
  .pagenav button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .stage {
    position: relative;
    align-self: center;
    max-width: 100%;
    line-height: 0;
    border-radius: var(--r-md);
    overflow: hidden;
    background: oklch(1 0 0);
    box-shadow: var(--shadow-1);
    touch-action: none;
  }
  .stage.manual {
    cursor: crosshair;
  }
  .stage img {
    display: block;
    max-width: 100%;
    max-height: 62vh;
    user-select: none;
    -webkit-user-drag: none;
  }

  .cropbox {
    position: absolute;
    border: 2px solid var(--primary);
    background: var(--primary-quiet);
    cursor: move;
    box-shadow: 0 0 0 100vmax oklch(0 0 0 / 0.45);
  }
  .cropbox:focus-visible {
    outline: 2px solid var(--focus);
    outline-offset: 1px;
  }
  .handle {
    position: absolute;
    width: 14px;
    height: 14px;
    background: var(--primary);
    border: 2px solid var(--on-primary);
    border-radius: 3px;
  }
  .handle[data-handle='nw'] { left: -8px; top: -8px; cursor: nwse-resize; }
  .handle[data-handle='ne'] { right: -8px; top: -8px; cursor: nesw-resize; }
  .handle[data-handle='sw'] { left: -8px; bottom: -8px; cursor: nesw-resize; }
  .handle[data-handle='se'] { right: -8px; bottom: -8px; cursor: nwse-resize; }

  .hint {
    margin: var(--sp-3) 0 0;
    font-size: var(--fs-xs);
    color: var(--ink-faint);
    text-align: center;
  }
</style>
