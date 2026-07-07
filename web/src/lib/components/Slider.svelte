<script lang="ts">
  interface Props {
    label: string
    value: number
    min?: number
    max?: number
    step?: number
    hint?: string
    oninput: (value: number) => void
  }
  let { label, value, min = 0, max = 255, step = 1, hint, oninput }: Props = $props()
</script>

<div class="row">
  <span class="ctl-label">{label}</span>
  <input
    class="num mono"
    type="number"
    {min}
    {max}
    {step}
    {value}
    oninput={(e) => oninput(Number(e.currentTarget.value))}
    aria-label="{label} value"
  />
</div>
<input
  class="range"
  type="range"
  {min}
  {max}
  {step}
  {value}
  oninput={(e) => oninput(Number(e.currentTarget.value))}
  aria-label={label}
/>
{#if hint}<p class="hint">{hint}</p>{/if}

<style>
  .row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: var(--sp-2);
  }
  .ctl-label {
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--ink-muted);
  }
  .num {
    width: 4ch;
    padding: 2px 4px;
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-sm);
    text-align: right;
    -moz-appearance: textfield;
  }
  .num::-webkit-outer-spin-button,
  .num::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  .range {
    width: 100%;
    height: 24px;
    margin: 0;
    accent-color: var(--primary);
    cursor: pointer;
  }
  .hint {
    margin: var(--sp-1) 0 0;
    font-size: var(--fs-xs);
    color: var(--ink-faint);
  }
</style>
