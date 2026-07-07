<script lang="ts">
  import { editor, printLabel, scheduleRender } from '../editor.svelte'
  import { toast } from '../toast.svelte'
  import Button from './Button.svelte'
  import SegmentedControl from './SegmentedControl.svelte'
  import Slider from './Slider.svelte'

  interface Props {
    onSaveProfile: () => void
    onPrinted: () => void
  }
  let { onSaveProfile, onPrinted }: Props = $props()

  function set<K extends keyof typeof editor>(key: K, value: (typeof editor)[K]) {
    editor[key] = value
    scheduleRender()
  }

  async function print() {
    const res = await printLabel()
    toast(res.ok ? '✓ ' + res.detail : 'Print failed: ' + res.detail, res.ok ? 'ok' : 'err')
    if (res.ok) onPrinted()
  }

  function reset() {
    editor.rotate = 0
    editor.threshold = 128
    editor.cropMode = 'profile'
    scheduleRender()
  }
</script>

<div class="panel">
  <div class="field">
    <span class="ctl-label">Profile</span>
    <div class="select-wrap">
      <select value={editor.profile} onchange={(e) => set('profile', e.currentTarget.value)}>
        {#each editor.profiles as p (p.name)}
          <option value={p.name}>{p.name} — {p.description || p.page_type}</option>
        {/each}
      </select>
      <span class="chevron" aria-hidden="true">▾</span>
    </div>
  </div>

  <div class="field">
    <SegmentedControl
      label="Crop"
      value={editor.cropMode}
      options={[
        { value: 'profile', label: 'Profile' },
        { value: 'auto', label: 'Auto' },
        { value: 'manual', label: 'Manual' },
        { value: 'none', label: 'None' },
      ]}
      onchange={(v) => set('cropMode', v as typeof editor.cropMode)}
    />
    {#if editor.cropMode === 'manual'}
      <button class="link" onclick={onSaveProfile}>Save crop as profile…</button>
    {/if}
  </div>

  <div class="field">
    <SegmentedControl
      label="Rotate"
      value={String(editor.rotate)}
      options={[
        { value: '0', label: '0°' },
        { value: '90', label: '90°' },
        { value: '180', label: '180°' },
        { value: '270', label: '270°' },
      ]}
      onchange={(v) => set('rotate', Number(v))}
    />
  </div>

  <div class="field">
    <Slider
      label="Threshold"
      value={editor.threshold}
      hint="Lower = less ink · higher = only darkest marks"
      oninput={(v) => set('threshold', v)}
    />
  </div>

  <div class="actions">
    <Button variant="primary" loading={editor.printing} onclick={print}>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2" />
        <rect x="6" y="14" width="12" height="8" rx="1" />
      </svg>
      Print
    </Button>
    <Button variant="ghost" size="md" title="Reset adjustments" onclick={reset}>↺</Button>
  </div>
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: var(--sp-5);
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
  }
  .ctl-label {
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--ink-muted);
  }
  .select-wrap {
    position: relative;
  }
  select {
    width: 100%;
    min-height: var(--tap);
    padding: 0 var(--sp-8) 0 var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-base);
    appearance: none;
    cursor: pointer;
  }
  select:hover {
    border-color: var(--line-strong);
  }
  .chevron {
    position: absolute;
    right: var(--sp-3);
    top: 50%;
    transform: translateY(-50%);
    color: var(--ink-faint);
    pointer-events: none;
  }
  .link {
    align-self: flex-start;
    border: none;
    background: none;
    padding: var(--sp-1) 0;
    color: var(--primary);
    font-size: var(--fs-sm);
    cursor: pointer;
  }
  .link:hover {
    text-decoration: underline;
  }
  .actions {
    display: flex;
    gap: var(--sp-2);
    margin-top: var(--sp-2);
  }
  .actions :global(.btn.primary) {
    flex: 1;
  }
</style>
