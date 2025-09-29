(() => {
  const API_BASE = ""; // same host

  // Elements
  const filterRole = document.getElementById('filterRole');
  const filterLocation = document.getElementById('filterLocation');
  const filterSkill = document.getElementById('filterSkill');
  const filterCategory = document.getElementById('filterCategory');
  const filterGlobal = document.getElementById('filterGlobal');
  const resultsTableBody = document.querySelector('#resultsTable tbody');
  const resultCount = document.getElementById('resultCount');
  const pageInfo = document.getElementById('pageInfo');
  const prevPageBtn = document.getElementById('prevPage');
  const nextPageBtn = document.getElementById('nextPage');
  const btnSearch = document.getElementById('btnSearch');
  const btnReset = document.getElementById('btnReset');
  const uploadFile = document.getElementById('uploadFile');
  const uploadCategory = document.getElementById('uploadCategory');
  const btnUpload = document.getElementById('btnUpload');
  const viewTable = document.getElementById('viewTable');
  const viewCategories = document.getElementById('viewCategories');
  const btnViewTable = document.getElementById('btnViewTable');
  const btnViewCategories = document.getElementById('btnViewCategories');
  const categoriesGrid = document.getElementById('categoriesGrid');
  const loading = document.getElementById('loading');

  // State
  let skip = 0;
  let limit = 20;
  let lastBatchCount = 0;

  function buildQueryParams() {
    const params = new URLSearchParams();
    if (filterGlobal.value) params.append('q', filterGlobal.value);
    if (filterRole.value) params.append('role', filterRole.value);
    if (filterLocation.value) params.append('location', filterLocation.value);
    if (filterSkill.value) params.append('skill', filterSkill.value);
    if (filterCategory.value) params.append('category', filterCategory.value);
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return params.toString();
  }

  function renderSkills(skills) {
    if (!skills || !skills.length) return '';
    const MAX = 6;
    const limited = skills.slice(0, MAX).map(s => `<span class="badge badge-skill">${escapeHtml(s)}</span>`).join('');
    const more = skills.length > MAX ? `<button type="button" class="btn btn-sm btn-link p-0 ms-1 show-all-skills" data-skills="${encodeURIComponent(JSON.stringify(skills))}">See more</button>` : '';
    return limited + more;
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"]+/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
  }

  function renderRows(data) {
    resultsTableBody.innerHTML = data.map(p => {
      const profileUrl = p.profile_url || '#';
      const titleCell = truncateWithSeeMore(p.current_role || '');
      const educationCell = truncateWithSeeMore(((p.education || [])[0]?.institute) || '');
      const locationCell = truncateWithSeeMore(p.location || '');
      const categoryCell = truncateWithSeeMore(p.category || '');
      const skillsCell = truncateWithSeeMore((p.skills || []).join(', '));
      return `<tr>
        <td>${profileUrl ? `<a href="${profileUrl}" target="_blank" class="btn btn-sm btn-outline-primary">Open</a>` : ''}</td>
        <td class="truncate" title="${escapeHtml(p.name || '')}">${escapeHtml(p.name || '')}</td>
        <td>${titleCell}</td>
        <td>${educationCell}</td>
        <td>${locationCell}</td>
        <td>${categoryCell}</td>
        <td class="skill-wrap">${skillsCell}</td>
      </tr>`;
    }).join('');
    // bind show all skills
    resultsTableBody.querySelectorAll('.show-all-skills').forEach(btn => {
      btn.addEventListener('click', () => {
        const skills = JSON.parse(decodeURIComponent(btn.getAttribute('data-skills')));
        showSkillsModal(skills);
      });
    });
    // bind see more
    resultsTableBody.querySelectorAll('[data-see-more]').forEach(btn => {
      btn.addEventListener('click', () => {
        const content = decodeURIComponent(btn.getAttribute('data-see-more') || '');
        showTextModal(content);
      });
    });
  }

  function showSkillsModal(skills) {
    const markup = `
      <div class="modal fade" id="skillsModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Skills</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              ${skills.map(s => `<span class=\"badge badge-skill\">${escapeHtml(s)}</span>`).join(' ')}
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
          </div>
        </div>
      </div>`;

    let container = document.getElementById('skillsModal');
    if (container) container.remove();
    const wrapper = document.createElement('div');
    wrapper.innerHTML = markup;
    document.body.appendChild(wrapper.firstElementChild);
    const modal = new bootstrap.Modal(document.getElementById('skillsModal'));
    modal.show();
  }

  function truncateWithSeeMore(text) {
    const t = String(text || '');
    const MAX = 28;
    if (t.length <= MAX) return escapeHtml(t);
    const short = escapeHtml(t.slice(0, MAX)) + '… ';
    return `${short}<button type="button" class="btn btn-sm btn-link p-0" data-see-more="${encodeURIComponent(t)}">See more</button>`;
  }

  function showTextModal(text) {
    const markup = `
      <div class="modal fade" id="textModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Details</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body"><div class="text-wrap" style="white-space:pre-wrap;word-break:break-word;">${escapeHtml(text)}</div></div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
          </div>
        </div>
      </div>`;
    let container = document.getElementById('textModal');
    if (container) container.remove();
    const wrapper = document.createElement('div');
    wrapper.innerHTML = markup;
    document.body.appendChild(wrapper.firstElementChild);
    const modal = new bootstrap.Modal(document.getElementById('textModal'));
    modal.show();
  }

  async function fetchProfiles() {
    const q = buildQueryParams();
    let items = [];
    let total = 0;
    try {
      loading.classList.add('show');
      const res = await fetch(`${API_BASE}/api/profiles/search-adv?${q}`);
      if (!res.ok) throw new Error('adv failed');
      const data = await res.json();
      items = data.items || [];
      total = data.total || 0;
    } catch (e) {
      // Fallback to simple list endpoint
      const res2 = await fetch(`${API_BASE}/api/profiles?${q}`);
      if (!res2.ok) throw new Error('Failed to fetch profiles');
      items = await res2.json();
      total = skip + items.length; // unknown total
    } finally { loading.classList.remove('show'); }
    lastBatchCount = items.length;
    resultCount.textContent = `${total}`;
    const currentPage = Math.floor(skip / limit) + 1;
    const totalPages = Math.max(1, Math.ceil(total / limit));
    pageInfo.textContent = `Page ${currentPage}/${totalPages}`;
    renderRows(items);
    prevPageBtn.disabled = skip === 0;
    nextPageBtn.disabled = items.length < limit;
  }

  async function fetchCategories() {
    const res = await fetch(`${API_BASE}/api/profiles/by-category?limit=6`);
    if (!res.ok) throw new Error('Failed to fetch categories');
    const data = await res.json();
    categoriesGrid.innerHTML = Object.entries(data).map(([cat, info]) => {
      const count = info.count || 0;
      const sample = (info.profiles || []).slice(0,3).map(p => `<div class="small text-muted truncate">${escapeHtml(p.name || '')} — ${escapeHtml(p.current_company || '')}</div>`).join('');
      return `<div class="col-md-4 col-lg-3 mb-3">
        <div class="category-card">
          <div class="d-flex justify-content-between align-items-start">
            <h6 class="mb-1">${escapeHtml(cat)}</h6>
            <span class="badge text-bg-primary">${count}</span>
          </div>
          <div class="mt-2">${sample || '<span class="text-muted">No samples</span>'}</div>
          <div class="mt-3 d-flex gap-2">
            <button class="btn btn-sm btn-outline-primary" data-cat="${escapeHtml(cat)}">Filter</button>
          </div>
        </div>
      </div>`;
    }).join('');

    // Bind filter buttons
    categoriesGrid.querySelectorAll('button[data-cat]').forEach(btn => {
      btn.addEventListener('click', () => {
        filterCategory.value = btn.getAttribute('data-cat') || '';
        showTable();
        onSearch();
      });
    });
  }

  function onSearch(evt) {
    if (evt) evt.preventDefault();
    skip = 0;
    fetchProfiles().catch(console.error);
  }

  function onReset() {
    filterRole.value = '';
    filterLocation.value = '';
    filterSkill.value = '';
    filterCategory.value = '';
    skip = 0;
    fetchProfiles().catch(console.error);
  }

  function showTable() {
    viewTable.style.display = '';
    viewCategories.style.display = 'none';
    btnViewTable.classList.add('btn-light');
    btnViewTable.classList.remove('btn-outline-light');
    btnViewCategories.classList.remove('btn-light');
    btnViewCategories.classList.add('btn-outline-light');
  }

  function showCategories() {
    viewTable.style.display = 'none';
    viewCategories.style.display = '';
    btnViewCategories.classList.add('btn-light');
    btnViewCategories.classList.remove('btn-outline-light');
    btnViewTable.classList.remove('btn-light');
    btnViewTable.classList.add('btn-outline-light');
    fetchCategories().catch(console.error);
  }

  // Pagination
  prevPageBtn.addEventListener('click', () => {
    if (skip === 0) return;
    skip = Math.max(0, skip - limit);
    fetchProfiles().catch(console.error);
  });
  nextPageBtn.addEventListener('click', () => {
    if (lastBatchCount < limit) return;
    skip += limit;
    fetchProfiles().catch(console.error);
  });

  // Filters
  document.getElementById('filters').addEventListener('submit', onSearch);
  btnReset.addEventListener('click', onReset);

  // Instant search (debounced)
  function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }
  const instant = debounce(() => { skip = 0; fetchProfiles().catch(console.error); }, 350);
  [filterGlobal, filterRole, filterLocation, filterSkill, filterCategory].forEach(el => {
    el.addEventListener('input', instant);
  });

  // Upload
  btnUpload.addEventListener('click', async () => {
    const file = uploadFile.files[0];
    if (!file) {
      alert('Select a file first');
      return;
    }
    const form = new FormData();
    form.append('file', file);
    let url = `${API_BASE}/api/profiles/import`;
    const cat = uploadCategory.value.trim();
    if (cat) {
      const qp = new URLSearchParams({category: cat});
      url += `?${qp.toString()}`;
    }
    btnUpload.disabled = true;
    btnUpload.textContent = 'Uploading...';
    try {
      const res = await fetch(url, { method: 'POST', body: form });
      if (!res.ok) throw new Error('Upload failed');
      await res.json();
      alert('Import completed');
      onSearch();
    } catch (e) {
      alert(e.message || 'Upload error');
    } finally {
      btnUpload.disabled = false;
      btnUpload.textContent = 'Upload';
      uploadFile.value = '';
    }
  });

  // View toggles
  btnViewTable.addEventListener('click', showTable);
  btnViewCategories.addEventListener('click', showCategories);

  // Initial load
  showTable();
  fetchProfiles().catch(console.error);
})();


