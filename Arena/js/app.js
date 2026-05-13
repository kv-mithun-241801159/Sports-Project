// ══════════════════════════════════════════
// app.js
// Main entry point — bootstraps the application
// ══════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

  // ── Close modal when clicking the backdrop ──────────────
  const modalOverlay = document.getElementById('modal');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) closeModal();
    });
  }

  // ── Close modal on Escape key ───────────────────────────
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  console.log('%c ARENA Tournament OS loaded ✓', 'color:#f5a623;font-weight:bold;font-size:14px');
});
