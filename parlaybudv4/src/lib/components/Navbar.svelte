<script lang="ts">
  import { page } from '$app/stores';

  let menuOpen = false;

  const links = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/history', label: 'History', icon: '📅' },
    { href: '/model', label: 'Model', icon: '🧠' }
  ];
</script>

<nav class="navbar">
  <div class="container nav-inner">
    <a href="/" class="logo">
      <span class="logo-icon">🏀</span>
      <span class="logo-text">ParlayBud</span>
    </a>

    <div class="nav-links" class:open={menuOpen}>
      {#each links as link}
        <a
          href={link.href}
          class="nav-link"
          class:active={$page.url.pathname === link.href}
          on:click={() => menuOpen = false}
        >
          <span class="nav-icon">{link.icon}</span>
          <span class="nav-label">{link.label}</span>
        </a>
      {/each}
    </div>

    <button class="hamburger" on:click={() => menuOpen = !menuOpen} aria-label="Menu">
      <span class:open={menuOpen}></span>
      <span class:open={menuOpen}></span>
      <span class:open={menuOpen}></span>
    </button>
  </div>
</nav>

<style>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.logo-icon { font-size: 1.5rem; }

.logo-text {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 1.2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  transition: all var(--transition);
  text-decoration: none;
}

.nav-link:hover {
  color: var(--text);
  background: rgba(255,255,255,0.06);
}

.nav-link.active {
  color: var(--primary);
  background: rgba(59,130,246,0.12);
}

.nav-icon { font-size: 1rem; }

.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  padding: 8px;
  background: none;
  border: none;
  cursor: pointer;
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--text-muted);
  border-radius: 2px;
  transition: all var(--transition);
}

.hamburger span.open:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
.hamburger span.open:nth-child(2) { opacity: 0; }
.hamburger span.open:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }

@media (max-width: 640px) {
  .hamburger { display: flex; }

  .nav-links {
    display: none;
    position: absolute;
    top: 64px;
    left: 0;
    right: 0;
    flex-direction: column;
    background: rgba(15, 23, 42, 0.98);
    backdrop-filter: blur(16px);
    padding: 1rem;
    border-bottom: 1px solid var(--card-border);
    gap: 4px;
  }

  .nav-links.open { display: flex; }
  .nav-link { width: 100%; padding: 12px 16px; }
}
</style>
