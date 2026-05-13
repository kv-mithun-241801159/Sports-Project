// ══════════════════════════════════════════
// modal.js
// Controls the Create Tournament modal and toast
// ══════════════════════════════════════════

/**
 * Open the Create Tournament modal.
 */
function openModal() {
  document.getElementById('modal').classList.add('open');
}

/**
 * Close the Create Tournament modal.
 */
function closeModal() {
  document.getElementById('modal').classList.remove('open');
}

/**
 * Handle tournament creation form submission.
 * Shows a toast confirmation on success.
 */
function createTournament() {
  const nameInput = document.getElementById('new-name');
  const name      = nameInput ? nameInput.value.trim() : '';

  closeModal();
  showToast(name ? `🏆 "${name}" created successfully!` : '🏆 Tournament created successfully!');
}

/**
 * Show a toast notification for a given duration.
 *
 * @param {string} message   - Text to display
 * @param {number} [duration=3000] - Milliseconds before hiding
 */
function showToast(message, duration = 3000) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => toast.classList.remove('show'), duration);
}
