<script lang="ts">
  import reports from '#lib/data/reports-4471.json';
  import notes from '#lib/data/desk-notes.json';
  import type { Report } from '#lib/kb/causes';
  import { tenantOf } from '#lib/kb/locales';
  import { groupByProblem } from '#lib/kb/problems';

  let { ticket }: { ticket: number } = $props();

  // Counted at render time, so the table follows the desk as it keeps merging.
  const view = $derived(groupByProblem(reports as Report[], ticket, tenantOf, notes.oneDayMove));
</script>

<p class="sum">
  <strong>{view.total}</strong> reports merged into #{ticket} · <strong>{view.groups.length}</strong>
  {view.groups.length === 1 ? 'problem' : 'problems'}
</p>

<table>
  <thead><tr><th>problem</th><th>reports</th><th>tenants</th><th>seen</th></tr></thead>
  <tbody>
    {#each view.groups as g (g.problem)}
      <tr>
        <td><code>{g.problem}</code></td>
        <td>{g.ids.length}</td>
        <td>{g.tenants.length}</td>
        <td>{g.firstSeen} → {g.lastSeen}</td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
  .sum { font-size: 1.1rem; }
</style>
