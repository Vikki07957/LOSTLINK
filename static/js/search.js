/**
 * LOSTLINK - Interactive Item Search & Filtering Engine
 * Filters items client-side & server-side with debounce
 */

document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('searchQuery');
  const typeFilter = document.getElementById('filterType');
  const categoryFilter = document.getElementById('filterCategory');
  const locationFilter = document.getElementById('filterLocation');
  const sortFilter = document.getElementById('filterSort');
  const viewToggleGrid = document.getElementById('viewGridBtn');
  const viewToggleTable = document.getElementById('viewTableBtn');
  const gridContainer = document.getElementById('itemsGrid');
  const tableContainer = document.getElementById('itemsTable');
  const resultCount = document.getElementById('resultCount');

  // Switch between Card Grid and Table view
  if (viewToggleGrid && viewToggleTable && gridContainer && tableContainer) {
    viewToggleGrid.addEventListener('click', () => {
      gridContainer.style.display = 'grid';
      tableContainer.style.display = 'none';
      viewToggleGrid.classList.add('btn-primary');
      viewToggleGrid.classList.remove('btn-outline-secondary');
      viewToggleTable.classList.remove('btn-primary');
      viewToggleTable.classList.add('btn-outline-secondary');
    });

    viewToggleTable.addEventListener('click', () => {
      gridContainer.style.display = 'none';
      tableContainer.style.display = 'block';
      viewToggleTable.classList.add('btn-primary');
      viewToggleTable.classList.remove('btn-outline-secondary');
      viewToggleGrid.classList.remove('btn-primary');
      viewToggleGrid.classList.add('btn-outline-secondary');
    });
  }

  // Client-side quick filter
  function filterItems() {
    const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
    const selectedType = typeFilter ? typeFilter.value.toLowerCase() : 'all';
    const selectedCategory = categoryFilter ? categoryFilter.value.toLowerCase() : 'all';
    const selectedLocation = (locationFilter ? locationFilter.value : '').toLowerCase().trim();

    const cards = document.querySelectorAll('.item-card-wrapper');
    const tableRows = document.querySelectorAll('.item-table-row');
    let visibleCount = 0;

    cards.forEach((card, idx) => {
      const title = card.getAttribute('data-title') || '';
      const desc = card.getAttribute('data-desc') || '';
      const type = card.getAttribute('data-type') || '';
      const category = card.getAttribute('data-category') || '';
      const location = card.getAttribute('data-location') || '';

      const matchQuery = !query || title.includes(query) || desc.includes(query) || location.includes(query);
      const matchType = selectedType === 'all' || type === selectedType;
      const matchCat = selectedCategory === 'all' || category === selectedCategory;
      const matchLoc = !selectedLocation || location.includes(selectedLocation);

      if (matchQuery && matchType && matchCat && matchLoc) {
        card.style.display = 'block';
        if (tableRows[idx]) tableRows[idx].style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
        if (tableRows[idx]) tableRows[idx].style.display = 'none';
      }
    });

    if (resultCount) {
      resultCount.innerText = visibleCount;
    }
  }

  if (searchInput) searchInput.addEventListener('input', filterItems);
  if (typeFilter) typeFilter.addEventListener('change', filterItems);
  if (categoryFilter) categoryFilter.addEventListener('change', filterItems);
  if (locationFilter) locationFilter.addEventListener('input', filterItems);
});
