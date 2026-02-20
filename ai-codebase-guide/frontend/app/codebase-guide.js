function toggleTheme() {
    const root = document.documentElement;
    const btn = document.getElementById('themeBtn');
    if (root.getAttribute('data-theme') === 'dark') {
      root.setAttribute('data-theme', 'light');
      btn.textContent = '☀️';
    } else {
      root.setAttribute('data-theme', 'dark');
      btn.textContent = '🌙';
    }
  }

  function switchTab(name, el) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
  }

  function selectQuick(btn, text) {
    document.querySelectorAll('.quick-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('askInput').value = text;
    document.getElementById('askInput').focus();
  }

  function handleUpload(input) {
    if (input.files.length > 0) {
      const notice = document.getElementById('uploadNotice');
      notice.textContent = `✓ ${input.files.length} file${input.files.length > 1 ? 's' : ''} uploaded`;
      notice.style.display = 'block';
      setTimeout(() => { notice.style.display = 'none'; }, 3000);
    }
  }

  // auto-resize textarea
  const ta = document.getElementById('askInput');
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  });