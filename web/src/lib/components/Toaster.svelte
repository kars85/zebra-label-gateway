<script lang="ts">
  import { fly } from 'svelte/transition'
  import { dismiss, toasts } from '../toast.svelte'
</script>

<div class="toaster" aria-live="polite">
  {#each toasts.items as t (t.id)}
    <button class="toast {t.kind}" onclick={() => dismiss(t.id)} transition:fly={{ y: 12, duration: 200 }}>
      {t.message}
    </button>
  {/each}
</div>

<style>
  .toaster {
    position: fixed;
    left: 50%;
    bottom: calc(var(--sp-6) + env(safe-area-inset-bottom));
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    z-index: var(--z-toast);
    pointer-events: none;
  }
  .toast {
    pointer-events: auto;
    max-width: min(90vw, 460px);
    padding: var(--sp-3) var(--sp-4);
    border: 1px solid var(--line);
    border-radius: var(--r-md);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-sm);
    text-align: left;
    box-shadow: var(--shadow-pop);
    cursor: pointer;
  }
  .toast.ok {
    border-color: var(--primary);
  }
  .toast.err {
    border-color: var(--err);
    color: var(--err);
  }
</style>
