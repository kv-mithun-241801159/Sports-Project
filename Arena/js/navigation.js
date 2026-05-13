// ══════════════════════════════════════════
// navigation.js
// Handles sidebar navigation and page switching
// ══════════════════════════════════════════

/**
 * Switch the visible page and update the active nav item.
 * Called via onclick="navigate('pageId', this)" in the sidebar.
 *
 * @param {string} page  - Key matching a PAGE_META entry and a #page-{page} element
 * @param {Element} el   - The clicked nav-item element
 */
function navigate(page, el) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  // Deactivate all nav items
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Show target page
  const targetPage = document.getElementById('page-' + page);
  if (targetPage) targetPage.classList.add('active');

  // Activate clicked nav item
  if (el) el.classList.add('active');

  // Update topbar title & subtitle
  const meta = PAGE_META[page];
  if (meta) {
    document.getElementById('page-title').textContent = meta.title;
    document.getElementById('page-sub').textContent   = meta.sub;
  }
}
