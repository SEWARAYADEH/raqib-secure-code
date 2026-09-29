/* Small, dependency-free interactions for the public corporate page. */
document.documentElement.classList.add('js');

const themeButton = document.querySelector('#theme-toggle');
const themeLabel = document.querySelector('#theme-label');
const themeColor = document.querySelector('meta[name="theme-color"]');

function setTheme(theme) {
  const dark = theme === 'dark';
  document.body.dataset.theme = dark ? 'dark' : 'light';
  themeButton.setAttribute('aria-pressed', String(dark));
  themeButton.setAttribute('aria-label', dark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي');
  themeLabel.textContent = dark ? 'نهاري' : 'ليلي';
  themeColor.setAttribute('content', dark ? '#081424' : '#e9f1fa');
}

try {
  setTheme(localStorage.getItem('raqib-public-theme') === 'light' ? 'light' : 'dark');
} catch {
  setTheme('dark');
}
themeButton.addEventListener('click', () => {
  const next = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
  setTheme(next);
  try { localStorage.setItem('raqib-public-theme', next); } catch { /* Storage can be unavailable. */ }
});

/* Smart header: keep navigation reachable on upward scroll and near the top. */
const header = document.querySelector('#site-header');
let previousY = window.scrollY;
let scrollScheduled = false;
window.addEventListener('scroll', () => {
  if (scrollScheduled) return;
  scrollScheduled = true;
  requestAnimationFrame(() => {
    const currentY = window.scrollY;
    header.classList.toggle('compact', currentY > 36);
    header.classList.toggle('hidden', currentY > 160 && currentY > previousY + 4);
    if (currentY < previousY - 4 || currentY < 160) header.classList.remove('hidden');
    previousY = currentY;
    scrollScheduled = false;
  });
}, { passive: true });

/* Mobile menu closes after a choice or Escape. */
const menuButton = document.querySelector('#menu-toggle');
const menu = document.querySelector('#nav-links');
function closeMenu() {
  menu.classList.remove('open');
  menuButton.setAttribute('aria-expanded', 'false');
}
menuButton.addEventListener('click', () => {
  const open = !menu.classList.contains('open');
  menu.classList.toggle('open', open);
  menuButton.setAttribute('aria-expanded', String(open));
});
menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeMenu();
});

/* Reveal is optional enhancement; content stays visible without observer support. */
const revealItems = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('visible'));
}

/* Horizontal stepper uses native scroll snapping and supports keyboard arrows. */
const processTrack = document.querySelector('#process-track');
const processCards = [...processTrack.querySelectorAll('.process-card')];
const previousButton = document.querySelector('#step-prev');
const nextButton = document.querySelector('#step-next');
const currentNumber = document.querySelector('#process-current');
const progress = document.querySelector('#process-progress');
let activeStep = 0;
function renderStep() {
  currentNumber.textContent = String(activeStep + 1).padStart(2, '0');
  progress.style.width = `${((activeStep + 1) / processCards.length) * 100}%`;
  previousButton.disabled = activeStep === 0;
  nextButton.disabled = activeStep === processCards.length - 1;
}
function goToStep(index) {
  activeStep = Math.max(0, Math.min(processCards.length - 1, index));
  processCards[activeStep].scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
  renderStep();
}
previousButton.addEventListener('click', () => goToStep(activeStep - 1));
nextButton.addEventListener('click', () => goToStep(activeStep + 1));
processTrack.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    goToStep(activeStep + (event.key === 'ArrowLeft' ? 1 : -1));
  }
});
processTrack.addEventListener('scroll', () => {
  const edge = processTrack.getBoundingClientRect().right;
  let closest = 0;
  let distance = Infinity;
  processCards.forEach((card, index) => {
    const value = Math.abs(edge - card.getBoundingClientRect().right);
    if (value < distance) { closest = index; distance = value; }
  });
  activeStep = closest;
  renderStep();
}, { passive: true });
renderStep();

/* Public capabilities come from the backend, never from a duplicated status list. */
const packDescriptions = {
  SQL_INJECTION: ['⌁', 'منع إدخال بيانات المستخدم في استعلامات SQL بطريقة غير آمنة.'],
  COMMAND_INJECTION: ['>_', 'كشف وصول المدخلات لأوامر النظام أو Shell.'],
  PATH_TRAVERSAL: ['↖', 'كشف مسارات قد تصل لملفات خارج النطاق المسموح.'],
  XSS: ['</>', 'كشف وصول مدخلات غير آمنة إلى HTML أو JavaScript.'],
  BROKEN_AUTHORIZATION_IDOR: ['◇', 'كشف وصول المستخدم لموارد خارج صلاحياته.'],
};
const packGrid = document.querySelector('#pack-grid');
const formatGrid = document.querySelector('#format-grid');
async function loadCapabilities() {
  try {
    const response = await fetch('/api/v1/analysis/options', { cache: 'no-store' });
    if (!response.ok) throw new Error('API unavailable');
    const options = await response.json();
    if (Array.isArray(options.workflow_stages)) {
      processCards.forEach((card, index) => {
        const stage = options.workflow_stages[index];
        if (!stage) return;
        card.querySelector('small').textContent = stage.status.replaceAll('_', ' ');
        card.classList.toggle('planned', stage.status === 'NOT_AVAILABLE');
      });
    }
    packGrid.replaceChildren();
    for (const pack of options.security_packs) {
      const card = document.createElement('article');
      card.className = 'focus-card';
      const icon = document.createElement('span');
      icon.className = 'focus-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = packDescriptions[pack.id]?.[0] ?? '◇';
      const title = document.createElement('h3');
      title.textContent = pack.display_name;
      const description = document.createElement('p');
      description.textContent = packDescriptions[pack.id]?.[1] ?? '';
      const status = document.createElement('small');
      const verified = pack.can_verify_exploitability && pack.can_generate_verified_patch && pack.can_close;
      status.textContent = verified ? 'Verification & Repair Available'
        : pack.status === 'NOT_IMPLEMENTED' ? 'Coming / In Development'
          : pack.status === 'PARTIAL_STATIC_CANDIDATES' ? 'Analysis Available' : 'Unknown';
      status.className = pack.status === 'NOT_IMPLEMENTED' ? 'pack-state planned' : 'pack-state';
      card.append(icon, title, description, status);
      packGrid.append(card);
    }
    const accepted = new Set(options.scopes.flatMap((scope) => scope.accept.split(',')));
    const formats = [['Python', '.py'], ['JavaScript', '.js'], ['JavaScript JSX', '.jsx'], ['Full Project', '.zip']];
    formatGrid.replaceChildren();
    for (const [name, extension] of formats) {
      if (!accepted.has(extension)) continue;
      const item = document.createElement('div');
      const label = document.createElement('strong');
      label.textContent = name;
      const suffix = document.createElement('code');
      suffix.textContent = extension;
      item.append(label, suffix);
      formatGrid.append(item);
    }
  } catch {
    packGrid.textContent = 'حالة الحزم غير متاحة الآن. شغّل Backend لعرض الدعم الفعلي.';
    formatGrid.textContent = 'أنواع الملفات غير متاحة الآن. شغّل Backend قبل الرفع.';
  }
}
void loadCapabilities();

/* Render only curated synthetic records returned by the local SQLite catalog. */
const exampleStatus = document.querySelector('#example-status');
const exampleGrid = document.querySelector('#example-grid');
async function loadExamples() {
  try {
    const response = await fetch('/api/v1/examples', { cache: 'no-store' });
    if (!response.ok) throw new Error('API unavailable');
    const payload = await response.json();
    if (!Array.isArray(payload.examples) || payload.examples.length === 0) {
      exampleStatus.textContent = 'قاعدة الأمثلة متاحة، لكن لم تُزرع حالات تقييم بعد.';
      return;
    }
    exampleStatus.textContent = `${payload.examples.length} حالات اصطناعية محفوظة · نتائج تحليل ساكن، دون إثبات استغلال`;
    for (const item of payload.examples) {
      const card = document.createElement('article');
      card.className = 'example-card';
      const category = document.createElement('small');
      category.textContent = `SQL INJECTION / ${item.classification}`;
      const title = document.createElement('h3');
      title.textContent = item.id;
      const summary = document.createElement('p');
      summary.textContent = `${item.candidate_count} مرشح · ${item.non_candidate_count} مسار لم يُرقّ إلى نتيجة`;
      const evidence = document.createElement('code');
      evidence.textContent = `SHA-256 ${item.source_sha256.slice(0, 16)}…`;
      card.append(category, title, summary, evidence);
      exampleGrid.append(card);
    }
  } catch {
    exampleStatus.textContent = 'تعذر الاتصال بقاعدة الأمثلة المحلية. شغّل Backend للتحقق منها.';
  }
}
void loadExamples();
