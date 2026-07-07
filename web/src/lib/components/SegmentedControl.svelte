<script lang="ts">
  interface Option {
    value: string
    label: string
  }
  interface Props {
    options: Option[]
    value: string
    label?: string
    onchange: (value: string) => void
  }
  let { options, value, label, onchange }: Props = $props()
</script>

{#if label}<span class="ctl-label">{label}</span>{/if}
<div class="seg" role="group" aria-label={label}>
  {#each options as opt (opt.value)}
    <button
      class="opt"
      class:on={opt.value === value}
      aria-pressed={opt.value === value}
      onclick={() => onchange(opt.value)}
    >
      {opt.label}
    </button>
  {/each}
</div>

<style>
  .ctl-label {
    display: block;
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--ink-muted);
    margin-bottom: var(--sp-2);
  }
  .seg {
    display: flex;
    gap: 2px;
    padding: 2px;
    background: var(--surface-2);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
  }
  .opt {
    flex: 1;
    min-height: 32px;
    padding: 0 var(--sp-2);
    border: none;
    border-radius: var(--r-sm);
    background: transparent;
    color: var(--ink-muted);
    font-size: var(--fs-sm);
    font-weight: 550;
    cursor: pointer;
    transition:
      background var(--dur-fast) var(--ease-out),
      color var(--dur-fast) var(--ease-out);
  }
  .opt:hover:not(.on) {
    color: var(--ink);
  }
  .opt.on {
    background: var(--primary);
    color: var(--on-primary);
  }
</style>
