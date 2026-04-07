/* ============================================================
   main.js — SIM Lab Komputer
   Global JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar Toggle (Mobile) ────────────────────────────
  const sidebar  = document.getElementById('sidebar');
  const toggle   = document.getElementById('sidebarToggle');
  const overlay  = document.getElementById('sidebarOverlay');
  const mainWrap = document.getElementById('mainWrapper');

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (toggle)  toggle.addEventListener('click', openSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // ── Date Display ───────────────────────────────────────
 const dateEl = document.getElementById('currentDate');

if (dateEl) {
  const now = new Date();

  dateEl.textContent = now.toLocaleDateString('id-ID', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'Asia/Jakarta'
  });
}

  // ── Auto-dismiss Flash Messages ────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.custom-alert').forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, 4000);

  // ── Stat card entrance animation ──────────────────────
  const statCards = document.querySelectorAll('.stat-card');
  statCards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'opacity .4s ease, transform .4s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 80 * i);
  });

});
