<script lang="ts">
  import { api, type HistoryEntry } from '../api'
  import { toast } from '../toast.svelte'

  let entries = $state<HistoryEntry[]>([])
  let loaded = $state(false)

  export async function refresh() {
    try {
      entries = await api.history()
    } catch {
      entries = []
    }
    loaded = true
  }

  $effect(() => {
    refresh()
  })

  async function reprint(id: string) {
    try {
      const res = await api.reprint(id)
      toast('✓ ' + res.detail, 'ok')
    } catch (e) {
      toast('Reprint failed: ' + (e instanceof Error ? e.message : String(e)), 'err')
    }
  }

  async function remove(id: string) {
    await api.deleteHistory(id).catch(() => {})
    refresh()
  }

  function when(iso: string) {
    const d = new Date(iso)
    return isNaN(+d) ? '' : d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
</script>

{#if loaded && entries.length}
  <section class="history">
    <h2 class="section-title">Recent labels <span class="count mono">{entries.length}</span></h2>
    <div class="grid">
      {#each entries as h (h.id)}
        <article class="card">
          <img src={h.preview_url} alt="Saved label {h.name}" loading="lazy" />
          <div class="meta">
            <div class="name" title={h.name}>{h.name}</div>
            <div class="detail mono">{h.profile}{h.page ? ` · p${h.page + 1}` : ''} · {when(h.created)}</div>
            <div class="actions">
              <button class="reprint" onclick={() => reprint(h.id)}>Reprint</button>
              <button class="del" onclick={() => remove(h.id)} aria-label="Delete {h.name}">Delete</button>
            </div>
          </div>
        </article>
      {/each}
    </div>
  </section>
{/if}

<style>
  .history {
    margin-top: var(--sp-10);
  }
  .section-title {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    font-size: var(--fs-md);
    margin-bottom: var(--sp-4);
  }
  .count {
    font-size: var(--fs-xs);
    color: var(--ink-faint);
    padding: 1px var(--sp-2);
    border: 1px solid var(--line);
    border-radius: var(--r-full);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: var(--sp-4);
  }
  .card {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--line);
    border-radius: var(--r-lg);
    overflow: hidden;
    background: var(--surface);
  }
  .card img {
    width: 100%;
    aspect-ratio: 812 / 1218;
    object-fit: contain;
    background: oklch(1 0 0);
    border-bottom: 1px solid var(--line);
  }
  .meta {
    display: flex;
    flex-direction: column;
    gap: var(--sp-2);
    padding: var(--sp-3);
  }
  .name {
    font-size: var(--fs-sm);
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .detail {
    font-size: var(--fs-xs);
    color: var(--ink-faint);
  }
  .actions {
    display: flex;
    gap: var(--sp-2);
    margin-top: var(--sp-1);
  }
  .actions button {
    flex: 1;
    min-height: 32px;
    border: 1px solid var(--line);
    border-radius: var(--r-sm);
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--fs-xs);
    cursor: pointer;
  }
  .reprint {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    font-weight: 600;
  }
  .del:hover {
    border-color: var(--err) !important;
    color: var(--err) !important;
  }
</style>
