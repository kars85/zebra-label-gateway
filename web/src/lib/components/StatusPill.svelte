<script lang="ts">
  import { api, printerProblems, type PrinterStatus } from '../api'

  interface Props {
    onclick?: () => void
  }
  let { onclick }: Props = $props()

  let status = $state<PrinterStatus | null>(null)
  let loading = $state(true)

  export async function refresh() {
    loading = true
    try {
      status = await api.status()
    } catch {
      status = null
    }
    loading = false
  }

  $effect(() => {
    refresh()
    const timer = setInterval(refresh, 30000)
    return () => clearInterval(timer)
  })

  const problems = $derived(printerProblems(status))
  const tone = $derived(!status || !status.ok ? 'err' : problems.length ? 'warn' : 'ok')
  const label = $derived.by(() => {
    if (loading && !status) return 'checking…'
    if (!status || !status.ok) return `offline · ${status?.printer ?? 'no printer'}`
    if (problems.length) return problems.map((p) => p.replace('_', ' ')).join(', ')
    return `ready · ${status.printer}`
  })
</script>

<button class="pill {tone}" class:live={loading} onclick={onclick} title="Printer status — click for details">
  <span class="dot" class:pulse={tone === 'ok' && loading}></span>
  <span class="text">{label}</span>
</button>

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-2);
    height: 34px;
    padding: 0 var(--sp-3);
    border: 1px solid var(--line);
    border-radius: var(--r-full);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-sm);
    cursor: pointer;
    transition: border-color var(--dur-fast) var(--ease-out);
  }
  .pill:hover {
    border-color: var(--line-strong);
  }
  .text {
    font-variant-numeric: tabular-nums;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex: none;
    background: var(--ink-faint);
  }
  .ok .dot {
    background: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-quiet);
  }
  .warn .dot {
    background: var(--warn);
    box-shadow: 0 0 0 3px var(--warn-quiet);
  }
  .err .dot {
    background: var(--err);
    box-shadow: 0 0 0 3px var(--err-quiet);
  }
  .warn {
    color: var(--warn);
  }
  .err {
    color: var(--err);
  }
  .pulse {
    animation: pulse 1.4s var(--ease-out) infinite;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
  }
</style>
