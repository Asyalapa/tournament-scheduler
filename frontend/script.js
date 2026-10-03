'use strict';

/* =========================================================
 * 1. Конфиг. Новая система = новый объект здесь + бэкенд.
 *    Форма, валидация и подсказки подхватят её сами.
 * ======================================================= */
const API_URL = '/api/schedule';

const TOURNAMENT_SYSTEMS = {
  round_robin: {
    id: 'round_robin',
    name: 'Каждый с каждым (круговая)',
    description: 'Каждая команда играет с каждой один раз',
    enabled: true,
    minTeams: 2,
  },
  olympic: {
    id: 'olympic',
    name: 'Олимпийская система (на вылет)',
    description: 'Проигравший выбывает из турнира',
    enabled: false,
    minTeams: 2,
  },
  swiss: {
    id: 'swiss',
    name: 'Швейцарская система',
    description: 'Для больших турниров с рейтингом',
    enabled: false,
    minTeams: 4,
  },
  double_elimination: {
    id: 'double_elimination',
    name: 'Двойной вылет',
    description: 'Выбываешь после двух поражений',
    enabled: false,
    minTeams: 4,
  },
};
const DEFAULT_SYSTEM = Object.values(TOURNAMENT_SYSTEMS).find((s) => s.enabled).id;

/* =========================================================
 * 2. Хранилище. try/catch: в приватном режиме Safari
 *    localStorage может бросать исключения.
 * ======================================================= */
const store = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      return v === null ? fallback : JSON.parse(v);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* квота/приватный режим — не критично */
    }
  },
};

/* =========================================================
 * 3. DOM и состояние
 * ======================================================= */
const $ = (id) => document.getElementById(id);
const el = {
  form: $('form'),
  teams: $('teams'),
  teamsError: $('teams-error'),
  add: $('add-team'),
  system: $('system'),
  systemHint: $('system-hint'),
  fields: $('fields'),
  submit: $('submit'),
  result: $('result'),
  section: $('result-section'),
  reset: $('reset'),
  theme: $('theme-toggle'),
};
const EMPTY_HTML = el.result.innerHTML;
const MIN_TEAMS = 2;

let teams = store.get('teams', ['', '']);
if (!Array.isArray(teams) || teams.length < MIN_TEAMS) teams = ['', ''];

/* =========================================================
 * 4. Тема
 * ======================================================= */
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const dark = theme === 'dark';
  el.theme.setAttribute('aria-pressed', String(dark));
  el.theme.setAttribute('aria-label', 'Тёмная тема');
}
el.theme.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try {
    localStorage.setItem('theme', next);
  } catch {
    /* ignore */
  }
});
// inline-скрипт читает «сырую» строку, поэтому дублируем без JSON.stringify
applyTheme(document.documentElement.dataset.theme || 'light');

/* =========================================================
 * 5. Команды
 * ======================================================= */
function renderTeams(focusIndex) {
  el.teams.replaceChildren(
    ...teams.map((name, i) => {
      const li = document.createElement('li');
      li.className = 'team';

      const input = document.createElement('input');
      input.className = 'input';
      input.type = 'text';
      input.value = name;
      input.placeholder = 'Например: Спартак';
      input.autocomplete = 'off';
      input.setAttribute('aria-label', `Команда ${i + 1}`);
      input.dataset.index = i;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn--ghost btn--remove';
      btn.textContent = '×';
      btn.setAttribute('aria-label', `Удалить команду ${i + 1}`);
      btn.disabled = teams.length <= MIN_TEAMS;
      btn.dataset.index = i;

      li.append(input, btn);
      return li;
    })
  );
  if (focusIndex !== undefined) el.teams.querySelectorAll('input')[focusIndex]?.focus();
}

function addTeam(atIndex = teams.length) {
  teams.splice(atIndex, 0, '');
  store.set('teams', teams);
  renderTeams(atIndex);
}

el.add.addEventListener('click', () => addTeam());

el.teams.addEventListener('input', (e) => {
  teams[+e.target.dataset.index] = e.target.value;
  store.set('teams', teams);
  clearTeamsError();
});

el.teams.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn--remove');
  if (!btn || teams.length <= MIN_TEAMS) return;
  const i = +btn.dataset.index;
  teams.splice(i, 1);
  store.set('teams', teams);
  renderTeams(Math.min(i, teams.length - 1)); // фокус не теряется после удаления
});

el.teams.addEventListener('keydown', (e) => {
  if (e.target.tagName !== 'INPUT') return;
  const i = +e.target.dataset.index;
  if (e.key === 'Enter' && !(e.ctrlKey || e.metaKey)) {
    e.preventDefault(); // иначе Enter отправит форму
    const next = el.teams.querySelectorAll('input')[i + 1];
    next ? next.focus() : addTeam();
  } else if (e.key === 'Escape') {
    e.target.value = '';
    teams[i] = '';
    store.set('teams', teams);
  }
});

function clearTeamsError() {
  el.teamsError.textContent = '';
  el.teams.querySelectorAll('input').forEach((inp) => {
    inp.removeAttribute('aria-invalid');
    inp.removeAttribute('aria-describedby');
  });
}

/* =========================================================
 * 6. Система турнира и параллельные поля
 * ======================================================= */
function renderSystems() {
  el.system.replaceChildren(
    ...Object.values(TOURNAMENT_SYSTEMS).map((s) => {
      const o = new Option(s.enabled ? s.name : `${s.name} — скоро`, s.id);
      o.disabled = !s.enabled;
      o.title = s.description;
      return o;
    })
  );
  const saved = store.get('system', DEFAULT_SYSTEM);
  el.system.value = TOURNAMENT_SYSTEMS[saved]?.enabled ? saved : DEFAULT_SYSTEM;
  updateSystemHint();
}
function updateSystemHint() {
  el.systemHint.textContent = TOURNAMENT_SYSTEMS[el.system.value].description;
}
el.system.addEventListener('change', () => {
  store.set('system', el.system.value);
  updateSystemHint();
});

// Пусто или < 1 → подставляем 1 (по ТЗ)
function normalizeFields() {
  const n = parseInt(el.fields.value, 10);
  el.fields.value = Number.isFinite(n) && n >= 1 ? n : 1;
  store.set('fields', +el.fields.value);
  return +el.fields.value;
}
el.fields.value = store.get('fields', 2);
el.fields.addEventListener('change', normalizeFields);

/* =========================================================
 * 7. Валидация. Ошибка озвучивается через aria-describedby + role=alert.
 * ======================================================= */
function validate() {
  const system = TOURNAMENT_SYSTEMS[el.system.value];
  const names = teams.map((t) => t.trim());
  const filled = names.filter(Boolean);
  const inputs = [...el.teams.querySelectorAll('input')];
  let message = '';
  let bad = [];

  if (filled.length < system.minTeams) {
    message = `Нужно ввести минимум ${system.minTeams} команды`;
    bad = inputs.filter((_, i) => !names[i]);
  } else {
    const seen = new Map();
    names.forEach((n, i) => {
      if (n) seen.set(n.toLowerCase(), [...(seen.get(n.toLowerCase()) || []), i]);
    });
    const dupes = [...seen.values()].filter((idx) => idx.length > 1).flat();
    if (dupes.length) {
      message = 'Названия команд не должны повторяться';
      bad = dupes.map((i) => inputs[i]);
    }
  }
  if (!message) return { ok: true, teams: filled };

  el.teamsError.textContent = message;
  bad.forEach((inp) => {
    inp.setAttribute('aria-invalid', 'true');
    inp.setAttribute('aria-describedby', 'teams-error');
  });
  (bad[0] || inputs[0]).focus();
  return { ok: false };
}

/* =========================================================
 * 8. Отправка и результат
 * ======================================================= */
function setLoading(on) {
  el.submit.disabled = on;
  el.submit.textContent = on ? 'Генерация...' : 'Составить расписание';
  el.result.setAttribute('aria-busy', String(on));
}

function showError(msg) {
  const p = document.createElement('p');
  p.className = 'error';
  p.setAttribute('role', 'alert');
  p.textContent = msg;
  el.result.replaceChildren(p);
}

function humanizeError(err, res) {
  if (err)
    return 'Не удалось связаться с сервером. Проверьте, что он запущен, и попробуйте ещё раз.';
  return res?.message || 'Что-то пошло не так. Проверьте данные и попробуйте ещё раз.';
}

el.form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearTeamsError();
  const fieldsCount = normalizeFields();
  const v = validate();
  if (!v.ok) return;

  setLoading(true);
  try {
    const resp = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        teams: v.teams,
        system: el.system.value,
        parallel_fields: fieldsCount,
      }),
    });
    const data = await resp.json().catch(() => null);
    if (!resp.ok || !data || data.status !== 'success')
      return showError(humanizeError(false, data));
    renderResult(data);
  } catch (err) {
    showError(humanizeError(err));
  } finally {
    setLoading(false);
  }
});

function renderResult({ schedule, stats }) {
  // const pct = Math.round((stats.efficiency ?? 0) * 100);
  const items = [
    ['Матчей', stats.total_matches],
    ['Слотов', stats.total_slots],
    ['Пауз', stats.rest_slots],
    // ['Эффективность', `${pct}%`],
  ];

  const wrap = document.createElement('div');
  wrap.className = 'result';

  const dl = document.createElement('dl');
  dl.className = 'stats';
  items.forEach(([k, v]) => {
    const d = document.createElement('div');
    d.className = 'stat';
    d.innerHTML = '<dt></dt><dd></dd>';
    d.firstChild.textContent = k;
    d.lastChild.textContent = v;
    dl.append(d);
  });

  const rows = schedule.map((s) => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    th.scope = 'row';
    th.textContent = s.slot;
    const td = document.createElement('td');
    if (s.type === 'match' && s.matches.length) {
      s.matches.forEach((m) => {
        const div = document.createElement('span');
        div.className = 'match';
        div.textContent = `${m.team1} — ${m.team2}`; // textContent: названия команд вводит пользователь, XSS нам не нужен
        td.append(div);
      });
    } else {
      tr.className = 'rest';
      td.textContent = 'Пауза';
    }
    tr.append(th, td);
    return tr;
  });

  const table = document.createElement('table');
  table.innerHTML =
    '<thead><tr><th scope="col">Слот</th><th scope="col">Матчи</th></tr></thead><tbody></tbody>';
  table.tBodies[0].append(...rows);
  const tw = document.createElement('div');
  tw.className = 'table-wrap';
  tw.tabIndex = 0; // скролл таблицы доступен с клавиатуры
  tw.setAttribute('role', 'region');
  tw.setAttribute('aria-label', 'Таблица расписания');
  tw.append(table);

  wrap.append(dl, tw);
  el.result.replaceChildren(wrap);
  el.reset.hidden = false;
  el.section.scrollIntoView({
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    block: 'start',
  });
}

el.reset.addEventListener('click', () => {
  el.result.innerHTML = EMPTY_HTML;
  el.reset.hidden = true;
  el.teams.querySelector('input')?.focus();
});

// Ctrl/Cmd + Enter — отправка из любого места формы
el.form.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    el.form.requestSubmit();
  }
});

/* =========================================================
 * 9. Старт
 * ======================================================= */
renderSystems();
renderTeams();
