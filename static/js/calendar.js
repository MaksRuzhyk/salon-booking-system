document.addEventListener('DOMContentLoaded', function () {
  const START_HOUR = 8;
  const END_HOUR = 21;
  const SLOT_MINUTES = 30;
  const mobileQuery = window.matchMedia('(max-width: 768px)');

  const state = {
    currentDate: startOfDay(new Date()),
    events: [],
    editingId: null,
    pendingDeleteId: null
  };

  const els = {
    top: document.getElementById('calendar-top'),
    body: document.getElementById('calendar-body'),

    status: document.getElementById('calendar-status'),
    overlay: document.getElementById('modal-overlay'),
    confirmOverlay: document.getElementById('confirm-overlay'),
    form: document.getElementById('appointment-form'),
    toastRegion: document.getElementById('toast-region')
  };

  const masterColors = [
    { bg: '#6e9ef5', fg: '#0e1624' },
    { bg: '#f57eb6', fg: '#1f0a14' },
    { bg: '#4ade80', fg: '#06210f' },
    { bg: '#fbbf24', fg: '#271700' }
  ];

  function viewDays() {
    return [startOfDay(state.currentDate)];
  }

  function renderCalendar() {
    const days = viewDays();
    renderHeader(days);
    renderBody(days);
    loadEvents(days);
  }

  function renderDateNav(container) {
    container.innerHTML = '';

    navDates().forEach(function (date) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'date-chip' + (sameDay(date, state.currentDate) ? ' active' : '') + (isToday(date) ? ' today' : '');
      button.setAttribute('aria-label', formatLongDate(date));
      button.setAttribute('aria-pressed', sameDay(date, state.currentDate) ? 'true' : 'false');
      button.appendChild(createEl('span', 'date-chip__weekday', formatWeekday(date)));
      button.appendChild(createEl('span', 'date-chip__day', String(date.getDate())));
      button.addEventListener('click', function () {
        state.currentDate = startOfDay(date);
        renderCalendar();
      });
      container.appendChild(button);
    });
  }

  function navDates() {
    const start = new Date(state.currentDate);
    start.setDate(start.getDate() - 2);
    return Array.from({ length: 7 }, function (_, index) {
      const date = new Date(start);
      date.setDate(start.getDate() + index);
      return startOfDay(date);
    });
  }
  function masterGridTemplate() {
    const minWidth = mobileQuery.matches ? 148 : 0;
    return `repeat(${Math.max(MASTERS.length, 1)}, minmax(${minWidth}px, 1fr))`;
  }

  function calendarContentMinWidth() {
    if (!mobileQuery.matches) return '';
    return Math.max(MASTERS.length, 1) * 148 + 'px';
  }
  function renderHeader(days) {
    els.top.innerHTML = '';
    els.top.appendChild(createEl('div', 'calendar-corner'));

    const daysWrap = createEl('div', 'calendar-days');
    daysWrap.style.gridTemplateColumns = `repeat(${days.length}, minmax(0, 1fr))`;

    days.forEach(function (day) {
      const dayHeader = createEl('div', 'calendar-day-header' + (isToday(day) ? ' today' : ''));
      const title = createEl('div', 'calendar-day-title calendar-day-title--nav');
      const dateNav = createEl('div', 'date-nav');
      dateNav.setAttribute('aria-label', 'Навігація по днях');
      renderDateNav(dateNav);
      title.appendChild(dateNav);
      dayHeader.appendChild(title);

      const mastersRow = createEl('div', 'master-header-row');
      mastersRow.style.gridTemplateColumns = `repeat(${Math.max(MASTERS.length, 1)}, minmax(0, 1fr))`;

      MASTERS.forEach(function (master) {
        mastersRow.appendChild(renderMasterHeader(master));
      });

      dayHeader.appendChild(mastersRow);
      daysWrap.appendChild(dayHeader);
    });

    els.top.appendChild(daysWrap);
  }

  function renderMasterHeader(master) {
    const header = createEl('div', 'master-header');
    const avatar = createEl('div', 'master-avatar');

    if (master.photoUrl) {
      const img = document.createElement('img');
      img.src = master.photoUrl;
      img.alt = '';
      avatar.appendChild(img);
    } else {
      avatar.textContent = master.initial || '?';
    }

    const info = createEl('div', 'master-info');
    info.appendChild(createEl('span', 'master-name', master.name));
    info.appendChild(createEl('span', 'master-role', 'Майстер'));

    header.appendChild(avatar);
    header.appendChild(info);

    if (master.isCurrentUser) {
      header.appendChild(createEl('span', 'master-badge', 'Ви'));
    }

    return header;
  }

  function renderBody(days) {
    els.body.innerHTML = '';
    const totalHeight = ((END_HOUR - START_HOUR) * getHourHeight()) + 'px';

    const axis = createEl('div', 'time-axis');
    axis.style.height = totalHeight;
    for (let hour = START_HOUR; hour < END_HOUR; hour += 1) {
      axis.appendChild(createEl('div', 'time-slot-label', pad(hour) + ':00'));
    }

    const grid = createEl('div', 'calendar-grid');
    grid.style.gridTemplateColumns = `repeat(${days.length}, minmax(0, 1fr))`;
    grid.style.height = totalHeight;

    days.forEach(function (day) {
      const dayColumn = createEl('div', 'day-column');
      dayColumn.style.gridTemplateColumns = `repeat(${Math.max(MASTERS.length, 1)}, minmax(0, 1fr))`;
      dayColumn.style.height = totalHeight;

      MASTERS.forEach(function (master) {
        const lane = createEl('div', 'master-lane' + (isToday(day) ? ' today' : ''));
        lane.dataset.date = toDateInput(day);
        lane.dataset.masterId = master.id;
        lane.style.height = totalHeight;
        lane.addEventListener('click', handleLaneClick);
        dayColumn.appendChild(lane);
      });

      grid.appendChild(dayColumn);
    });

    els.body.appendChild(axis);
    els.body.appendChild(grid);
    renderNowLine(days);
  }

  function renderEvents(days) {
    clearEvents();

    if (!MASTERS.length) {
      setStatus('Немає майстрів для відображення календаря.', 'empty');
      return;
    }

    if (!state.events.length) {
      hideStatus();
      return;
    }

    hideStatus();

    state.events.forEach(function (event) {
      const date = event.start.slice(0, 10);
      const lane = els.body.querySelector(`.master-lane[data-date="${date}"][data-master-id="${event.extendedProps.master_id}"]`);
      if (!lane) return;

      const masterIndex = Math.max(0, MASTERS.findIndex(function (m) { return String(m.id) === String(event.extendedProps.master_id); }));
      lane.appendChild(renderEvent(event, masterIndex));
    });
  }

  function renderEvent(event, masterIndex) {
    const start = event.start.slice(11, 16);
    const end = event.end.slice(11, 16);
    const startMinutes = timeToMinutes(start) - START_HOUR * 60;
    const endMinutes = timeToMinutes(end) - START_HOUR * 60;
    const top = minutesToPixels(Math.max(0, startMinutes));
    const height = Math.max(26, minutesToPixels(Math.max(SLOT_MINUTES, endMinutes - startMinutes)) - 4);
    const color = masterColors[masterIndex % masterColors.length];

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'calendar-event';
    button.style.top = top + 'px';
    button.style.height = height + 'px';
    button.style.background = color.bg;
    button.style.color = color.fg;
    button.addEventListener('click', function (e) {
      e.stopPropagation();
      openModal({
        id: event.id,
        date: event.start.slice(0, 10),
        startTime: start,
        endTime: end,
        procedure: event.extendedProps.procedure_id,
        clientName: event.extendedProps.client_name || '',
        masterId: event.extendedProps.master_id,
        isEdit: true
      });
    });

    button.appendChild(createEl('span', 'calendar-event__time', start + ' - ' + end));
    button.appendChild(createEl('span', 'calendar-event__title', event.title));
    if (event.extendedProps.client_name) {
      button.appendChild(createEl('span', 'calendar-event__meta', event.extendedProps.client_name));
    }

    return button;
  }

  function renderNowLine(days) {
    if (!days.some(isToday)) return;

    const now = new Date();
    const minutes = now.getHours() * 60 + now.getMinutes() - START_HOUR * 60;
    if (minutes < 0 || minutes > (END_HOUR - START_HOUR) * 60) return;

    const date = toDateInput(now);
    const lanes = els.body.querySelectorAll(`.master-lane[data-date="${date}"]`);
    lanes.forEach(function (lane) {
      const line = createEl('div', 'time-now-line');
      line.style.top = minutesToPixels(minutes) + 'px';
      lane.appendChild(line);
    });
  }

  function clearEvents() {
    els.body.querySelectorAll('.calendar-event, .time-now-line').forEach(function (node) {
      node.remove();
    });
    renderNowLine(viewDays());
  }

  function loadEvents(days) {
    if (!MASTERS.length) {
      renderEvents(days);
      return;
    }

    setStatus('Завантаження записів...');
    const start = toDateInput(days[0]) + 'T00:00:00';
    const lastDay = days[days.length - 1];
    const endDate = new Date(lastDay);
    endDate.setDate(lastDay.getDate() + 1);
    const end = toDateInput(endDate) + 'T00:00:00';
    const url = APPOINTMENTS_URL + '?' + new URLSearchParams({ start: start, end: end }).toString();

    fetch(url)
      .then(function (response) {
        if (!response.ok) throw new Error('Не вдалося завантажити записи.');
        return response.json();
      })
      .then(function (events) {
        state.events = events;
        renderEvents(days);
      })
      .catch(function () {
        state.events = [];
        clearEvents();
        setStatus('Не вдалося завантажити записи. Оновіть сторінку або спробуйте пізніше.', 'error');
      });
  }

  function handleLaneClick(event) {
    if (event.target.closest('.calendar-event')) return;

    const lane = event.currentTarget;
    const rect = lane.getBoundingClientRect();
    const offsetY = Math.max(0, event.clientY - rect.top);
    const minutes = snapMinutes(pixelsToMinutes(offsetY));
    const startMinutes = START_HOUR * 60 + minutes;

    openModal({
      date: lane.dataset.date,
      startTime: minutesToTime(startMinutes),
      masterId: lane.dataset.masterId
    });
  }

  function openModal(opts) {
    opts = opts || {};
    state.editingId = opts.id || null;

    document.getElementById('modal-title').textContent = opts.isEdit ? 'Редагувати запис' : 'Новий запис';
    document.getElementById('field-appointment-id').value = opts.id || '';
    document.getElementById('field-master').value = opts.masterId || CURRENT_USER_ID || (MASTERS[0] && MASTERS[0].id) || '';
    document.getElementById('field-date').value = opts.date || toDateInput(new Date());
    document.getElementById('field-start').value = opts.startTime || '';
    document.getElementById('field-end').value = opts.endTime || '';
    document.getElementById('field-client').value = opts.clientName || '';
    document.getElementById('field-procedure').value = opts.procedure || '';

    const deleteBtn = document.getElementById('delete-btn');
    deleteBtn.style.display = opts.isEdit ? 'inline-flex' : 'none';
    deleteBtn.onclick = opts.isEdit ? function () { openConfirm(opts.id); } : null;

    els.overlay.classList.add('active');
    document.getElementById('field-start').focus();
  }

  function closeModal() {
    els.overlay.classList.remove('active');
    els.form.reset();
    state.editingId = null;
  }

  function openConfirm(id) {
    state.pendingDeleteId = id;
    els.confirmOverlay.classList.add('active');
  }

  function closeConfirm() {
    els.confirmOverlay.classList.remove('active');
    state.pendingDeleteId = null;
  }

  function deleteAppointment() {
    if (!state.pendingDeleteId) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(DELETE_URL + state.pendingDeleteId + '/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken }
    })
      .then(function (response) {
        if (!response.ok) throw new Error('delete failed');
        return response.json();
      })
      .then(function (data) {
        if (!data.success) throw new Error('delete failed');
        closeConfirm();
        closeModal();
        showToast('Запис видалено.', 'success');
        loadEvents(viewDays());
      })
      .catch(function () {
        showToast('Не вдалося видалити запис.', 'error');
      });
  }

  function submitForm(event) {
    event.preventDefault();

    const data = new FormData(els.form);
    const appointmentId = document.getElementById('field-appointment-id').value;
    const url = appointmentId ? EDIT_URL + appointmentId + '/' : els.form.action;
    const submit = document.getElementById('modal-submit');
    submit.disabled = true;

    fetch(url, {
      method: 'POST',
      body: data,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          if (!response.ok || !payload.success) {
            throw payload;
          }
          return payload;
        });
      })
      .then(function () {
        closeModal();
        showToast(appointmentId ? 'Запис оновлено.' : 'Запис створено.', 'success');
        loadEvents(viewDays());
      })
      .catch(function (payload) {
        showToast(formErrorMessage(payload), 'error');
      })
      .finally(function () {
        submit.disabled = false;
      });
  }

  function calcEndTime() {
    const startVal = document.getElementById('field-start').value;
    const select = document.getElementById('field-procedure');
    const selected = select.options[select.selectedIndex];
    const duration = selected ? parseInt(selected.dataset.duration, 10) : 0;

    if (!startVal || !duration) return;
    document.getElementById('field-end').value = minutesToTime(timeToMinutes(startVal) + duration);
  }

  function setStatus(message, type) {
    els.status.textContent = message;
    els.status.className = 'calendar-status active' + (type ? ' ' + type : '');
  }

  function hideStatus() {
    els.status.className = 'calendar-status';
  }

  function showToast(message, type) {
    const toast = createEl('div', 'toast' + (type ? ' ' + type : ''), message);
    els.toastRegion.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 4200);
  }

  function formErrorMessage(payload) {
    if (!payload) return 'Не вдалося зберегти запис.';
    if (payload.error) return payload.error;
    if (payload.errors) {
      const firstKey = Object.keys(payload.errors)[0];
      const firstValue = payload.errors[firstKey];
      if (Array.isArray(firstValue) && firstValue.length) return firstValue[0];
      return 'Перевірте поля форми.';
    }
    return 'Не вдалося зберегти запис.';
  }


  function startOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }


  function isToday(date) {
    return toDateInput(date) === toDateInput(new Date());
  }

  function sameDay(first, second) {
    return toDateInput(first) === toDateInput(second);
  }

  function toDateInput(date) {
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    return year + '-' + month + '-' + day;
  }

  function formatWeekday(date) {
    return new Intl.DateTimeFormat('uk', { weekday: 'short' }).format(date);
  }

  function formatDayDate(date) {
    return new Intl.DateTimeFormat('uk', { day: 'numeric', month: 'short' }).format(date);
  }

  function formatDayMonth(date) {
    return new Intl.DateTimeFormat('uk', { day: 'numeric', month: 'long' }).format(date);
  }

  function formatLongDate(date) {
    return new Intl.DateTimeFormat('uk', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
  }

  function timeToMinutes(value) {
    const parts = value.split(':').map(Number);
    return parts[0] * 60 + parts[1];
  }

  function minutesToTime(total) {
    const normalized = Math.max(0, Math.min(23 * 60 + 59, total));
    return pad(Math.floor(normalized / 60)) + ':' + pad(normalized % 60);
  }

  function snapMinutes(minutes) {
    const snapped = Math.round(minutes / SLOT_MINUTES) * SLOT_MINUTES;
    return Math.max(0, Math.min((END_HOUR - START_HOUR) * 60 - SLOT_MINUTES, snapped));
  }

  function minutesToPixels(minutes) {
    return minutes / 60 * getHourHeight();
  }

  function pixelsToMinutes(px) {
    return px / getHourHeight() * 60;
  }

  function getHourHeight() {
    return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--calendar-hour-height')) || 56;
  }

  function pad(value) {
    return String(value).padStart(2, '0');
  }

  function createEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }


  document.getElementById('add-btn').addEventListener('click', function () {
    openModal({ masterId: CURRENT_USER_ID || (MASTERS[0] && MASTERS[0].id), date: toDateInput(state.currentDate) });
  });

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-cancel').addEventListener('click', closeModal);
  els.overlay.addEventListener('click', function (e) {
    if (e.target === els.overlay) closeModal();
  });

  document.getElementById('confirm-close').addEventListener('click', closeConfirm);
  document.getElementById('confirm-cancel').addEventListener('click', closeConfirm);
  document.getElementById('confirm-delete').addEventListener('click', deleteAppointment);
  els.confirmOverlay.addEventListener('click', function (e) {
    if (e.target === els.confirmOverlay) closeConfirm();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (els.confirmOverlay.classList.contains('active')) closeConfirm();
    else if (els.overlay.classList.contains('active')) closeModal();
  });

  document.getElementById('field-procedure').addEventListener('change', calcEndTime);
  document.getElementById('field-start').addEventListener('change', calcEndTime);
  els.form.addEventListener('submit', submitForm);

  if (mobileQuery.addEventListener) {
    mobileQuery.addEventListener('change', renderCalendar);
  } else {
    mobileQuery.addListener(renderCalendar);
  }

  renderCalendar();
});