// ══════════════════════════════════════════
// tabs.js
// Handles tab switching inside any .tabs container
// ══════════════════════════════════════════

/**
 * Attach click listeners to every .tab element.
 * When a tab is clicked, it becomes active within
 * its nearest .tabs parent (supports multiple tab groups).
 */
function initTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function () {
      // Deactivate all siblings in the same group
      this.closest('.tabs')
          .querySelectorAll('.tab')
          .forEach(t => t.classList.remove('active'));

      // Activate clicked tab
      this.classList.add('active');
    });
  });
}

// Initialise as soon as the DOM is ready
document.addEventListener('DOMContentLoaded', initTabs);
