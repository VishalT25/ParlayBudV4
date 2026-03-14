<script lang="ts">
  import '../app.css';
  import Navbar from '$lib/components/Navbar.svelte';
</script>

<Navbar />
<main class="main-content">
  <slot />
</main>

<footer class="site-footer">
  <div class="container">
    <p class="disclaimer">⚠️ For entertainment purposes only. Not financial advice. Gambling involves risk.</p>
    <p class="footer-note">ParlayBud V4 • XGBoost ML Models • 34,763 game logs</p>
  </div>
</footer>

<style>
.main-content {
  min-height: calc(100vh - 64px - 80px);
  padding-bottom: 2rem;
}

.site-footer {
  border-top: 1px solid var(--card-border);
  padding: 1.5rem 0;
  text-align: center;
}

.disclaimer {
  font-size: 12px;
  color: var(--accent-amber);
  margin-bottom: 4px;
}

.footer-note {
  font-size: 11px;
  color: var(--text-dim);
}
</style>
