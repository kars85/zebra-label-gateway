<script lang="ts">
  import type { Snippet } from 'svelte'

  interface Props {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md'
    type?: 'button' | 'submit'
    disabled?: boolean
    loading?: boolean
    title?: string
    onclick?: (e: MouseEvent) => void
    children: Snippet
  }
  let {
    variant = 'secondary',
    size = 'md',
    type = 'button',
    disabled = false,
    loading = false,
    title,
    onclick,
    children,
  }: Props = $props()
</script>

<button
  class="btn {variant} {size}"
  class:loading
  {type}
  {title}
  disabled={disabled || loading}
  onclick={onclick}
>
  {#if loading}<span class="spinner" aria-hidden="true"></span>{/if}
  <span class="content">{@render children()}</span>
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--sp-2);
    min-height: var(--tap);
    padding: 0 var(--sp-4);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-base);
    font-weight: 550;
    cursor: pointer;
    white-space: nowrap;
    transition:
      background var(--dur-fast) var(--ease-out),
      border-color var(--dur-fast) var(--ease-out),
      transform var(--dur-fast) var(--ease-out);
  }
  .btn.sm {
    min-height: 34px;
    padding: 0 var(--sp-3);
    font-size: var(--fs-sm);
  }
  .btn:hover:not(:disabled) {
    background: var(--line);
  }
  .btn:active:not(:disabled) {
    transform: translateY(1px);
  }
  .btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .primary {
    background: var(--primary);
    border-color: var(--primary);
    color: var(--on-primary);
    font-weight: 650;
  }
  .primary:hover:not(:disabled) {
    background: var(--primary-hover);
    border-color: var(--primary-hover);
  }

  .ghost {
    background: transparent;
    border-color: transparent;
  }
  .ghost:hover:not(:disabled) {
    background: var(--surface-2);
  }

  .danger:hover:not(:disabled) {
    background: var(--err-quiet);
    border-color: var(--err);
    color: var(--err);
  }

  .content {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-2);
  }
  .loading .content {
    opacity: 0.7;
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
