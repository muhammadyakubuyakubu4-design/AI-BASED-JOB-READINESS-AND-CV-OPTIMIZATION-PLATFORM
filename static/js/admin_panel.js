/* CareerAI Admin Panel — JavaScript */
document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar Toggle ──
  const sidebar = document.getElementById('apSidebar');
  const main = document.getElementById('apMain');
  const toggle = document.getElementById('apToggle');
  const close = document.getElementById('apSidebarClose');
  const overlay = document.getElementById('apOverlay');

  function openSidebar() {
    if (window.innerWidth < 992) {
      sidebar && sidebar.classList.add('mobile-open');
      overlay && overlay.classList.add('active');
    } else {
      sidebar && sidebar.classList.toggle('collapsed');
      main && main.classList.toggle('sidebar-collapsed');
      localStorage.setItem('ap_sidebar_collapsed', sidebar.classList.contains('collapsed'));
    }
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('mobile-open');
    overlay && overlay.classList.remove('active');
  }

  toggle && toggle.addEventListener('click', openSidebar);
  close && close.addEventListener('click', closeSidebar);
  overlay && overlay.addEventListener('click', closeSidebar);

  if (window.innerWidth >= 992 && localStorage.getItem('ap_sidebar_collapsed') === 'true') {
    sidebar && sidebar.classList.add('collapsed');
    main && main.classList.add('sidebar-collapsed');
  }

  // ── Dark Mode ──
  const themeToggle = document.getElementById('apThemeToggle');
  const themeIcon = document.getElementById('apThemeIcon');
  const html = document.documentElement;

  function applyTheme(t) {
    html.setAttribute('data-bs-theme', t);
    if (themeIcon) themeIcon.className = t === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    localStorage.setItem('ap_theme', t);
  }
  applyTheme(localStorage.getItem('ap_theme') || 'light');
  themeToggle && themeToggle.addEventListener('click', () => {
    applyTheme(html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark');
  });

  // ── Refresh button ──
  const refreshBtn = document.getElementById('apRefresh');
  refreshBtn && refreshBtn.addEventListener('click', function (e) {
    e.preventDefault();
    this.querySelector('i').classList.add('fa-spin');
    setTimeout(() => { this.querySelector('i').classList.remove('fa-spin'); }, 1000);
  });

  // ── Auto-dismiss alerts ──
  setTimeout(() => {
    document.querySelectorAll('.ap-alert').forEach(el => {
      const a = bootstrap.Alert.getOrCreateInstance(el);
      a && a.close();
    });
  }, 5000);

  // ── Confirm delete ──
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });

  // ── Tooltips ──
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));

  // ── Progress bar animation ──
  document.querySelectorAll('.ap-progress-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = w; }, 400);
  });

  // ── Search debounce ──
  const searchInputs = document.querySelectorAll('.ap-search-input[data-auto-submit]');
  searchInputs.forEach(input => {
    let timer;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => input.closest('form').submit(), 500);
    });
  });

});

// ── CSRF helper ──
function getCookie(name) {
  const v = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
  return v ? decodeURIComponent(v.split('=')[1]) : null;
}

// ── Chart helpers ──
const AP_COLORS = {
  green: '#1a8f5c', blue: '#0d6efd', yellow: '#ffc107',
  red: '#dc3545', cyan: '#0dcaf0', purple: '#6f42c1',
  orange: '#fd7e14', teal: '#20c997',
};

function apLineChart(id, labels, datasets, options = {}) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: datasets.length > 1 } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
      },
      ...options,
    },
  });
}

function apBarChart(id, labels, data, color = AP_COLORS.green, options = {}) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ data, backgroundColor: color + 'cc', borderColor: color, borderWidth: 2, borderRadius: 5 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
      },
      ...options,
    },
  });
}

function apDoughnutChart(id, labels, data, colors) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }] },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } } },
    },
  });
}
