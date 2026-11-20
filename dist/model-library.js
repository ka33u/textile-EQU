// The process stage stays the navigation key. Every selectable machine has its own asset ID.
export function machineHash(stageId, modelId, mode) {
  if (modelId && modelId !== stageId) return '#' + stageId + '/' + (mode === 'drive' ? 'drive' : 'model') + '/' + modelId;
  return '#' + stageId + (mode === 'drive' ? '/drive' : '');
}

export function parseMachineHash(hash, stages) {
  let parts;
  try { parts = decodeURIComponent(hash.replace(/^#/, '')).split('/'); }
  catch { return null; }
  const [current, view, model] = parts;
  if (!stages.some(stage => stage.id === current)) return null;
  const mode = view === 'drive' || view === 'motor' ? 'drive' : 'machine';
  const variant = parts.length > 2 && model !== current ? model : null;
  return {current, mode, variant};
}

function searchKey(text) {
  return String(text || '').normalize('NFKC').toLowerCase().replace(/[\s_–—-]/g, '');
}

export function filterModels(models, maker, stage, query = '') {
  const words = String(query).trim().split(/\s+/u).map(searchKey).filter(Boolean);
  return models.filter(item => {
    if ((maker && item.makerKey !== maker) || (stage && item.stageId !== stage)) return false;
    const text = searchKey([item.model, item.maker, item.makerKey, item.makerLabel, item.stageName, item.equipment].join(' '));
    return words.every(word => text.includes(word));
  });
}

function setOptions(select, choices) {
  select.replaceChildren(...choices.map(([value, label]) => new Option(label, value)));
}

export class ModelPicker {
  constructor(onPick, onRetry) {
    const get = id => document.getElementById(id);
    this.maker = get('machine-maker');
    this.model = get('machine-model');
    this.note = get('machine-options-note');
    this.dialog = get('model-library-dialog');
    this.filterMaker = get('library-maker');
    this.filterStage = get('library-stage');
    this.query = get('library-query');
    this.list = get('library-results');
    this.summary = get('library-summary');
    this.retry = get('library-retry');
    this.catalog = null;
    this.onPick = onPick;
    this.retry.addEventListener('click', onRetry);
    this.maker.addEventListener('change', () => {
      const choice = this.forStage().find(item => item.makerKey === this.maker.value);
      if (choice) onPick(choice);
    });
    this.model.addEventListener('change', () => {
      const choice = this.forStage().find(item => item.id === this.model.value);
      if (choice) onPick(choice);
    });
    for (const id of ['open-model-library', 'browse-model-library']) {
      get(id).addEventListener('click', () => {
        this.dialog.showModal();
        this.syncResults();
        this.query.focus();
      });
    }
    get('close-model-library').addEventListener('click', () => this.dialog.close());
    for (const field of [this.filterMaker, this.filterStage]) field.addEventListener('change', () => this.syncResults());
    this.query.addEventListener('input', () => this.syncResults());
    this.list.addEventListener('click', event => {
      const button = event.target.closest('[data-model]');
      const choice = this.catalog?.models.find(item => item.id === button?.dataset.model);
      if (choice) { this.dialog.close(); onPick(choice); }
    });
  }

  setCatalog(catalog) {
    this.catalog = catalog;
    this.retry.hidden = true;
    const stageNames = new Map(catalog.models.map(item => [item.stageId, item.stageName]));
    setOptions(this.filterMaker, [['', '全部厂家'], ...catalog.makers.map(item => [item.id, item.name])]);
    setOptions(this.filterStage, [['', '全部设备类别'], ...stageNames]);
    this.refresh(this.stageId, this.id);
    this.syncResults();
  }

  unavailable() {
    this.retry.hidden = false;
    this.note.textContent = '机型目录暂未载入';
    this.syncResults();
  }

  forStage() { return this.catalog?.models.filter(item => item.stageId === this.stageId) || []; }

  refresh(stageId, id) {
    this.stageId = stageId;
    this.id = id;
    if (!this.catalog) return;
    const local = this.forStage();
    const active = local.find(item => item.id === id);
    const makers = new Map(local.map(item => [item.makerKey, item.makerLabel]));
    setOptions(this.maker, [...makers]);
    this.maker.value = active?.makerKey || '';
    const sameMaker = local.filter(item => item.makerKey === active?.makerKey);
    setOptions(this.model, sameMaker.map(item => [item.id, item.model + (item.scope === 'station' ? ' · 公开工位' : '')]));
    this.model.value = active?.id || '';
    this.maker.disabled = makers.size <= 1 && !!active;
    this.model.disabled = sameMaker.length <= 1;
    this.note.textContent = local.length ? makers.size + ' 家厂商 · ' + local.length + ' 款机型' : '';
    if (this.dialog.open) this.syncResults();
  }

  syncResults() {
    this.list.replaceChildren();
    if (!this.catalog) {
      this.summary.textContent = this.retry.hidden ? '正在读取机型目录' : '机型目录暂未载入';
      return;
    }
    const hits = filterModels(this.catalog.models, this.filterMaker.value, this.filterStage.value, this.query.value)
      .sort((a, b) => Number(a.id === a.stageId) - Number(b.id === b.stageId));
    const stations = hits.filter(item => item.scope === 'station').length;
    this.summary.textContent = hits.length ? hits.length + ' 款机型 · ' + new Set(hits.map(x => x.makerKey)).size + ' 家厂商' + (stations ? ' · 含 ' + stations + ' 款公开工位模型' : '') : '未找到匹配机型，请调整筛选。';
    this.list.replaceChildren(...hits.map(item => {
      const li = document.createElement('li');
      const btn = document.createElement('button'); btn.type = 'button'; btn.dataset.model = item.id;
      btn.setAttribute('aria-current', item.id === this.id ? 'true' : 'false');
      const head = document.createElement('strong'); head.textContent = item.model;
      const context = document.createElement('span'); context.textContent = item.makerLabel + ' · ' + item.stageName;
      const description = document.createElement('small'); description.textContent = item.configuration;
      if (item.scope === 'station') {
        context.textContent += ' · ' + item.scopeLabel; context.classList.add('model-scope');
      }
      btn.append(context, head, description);
      if (item.id !== item.stageId && item.dating) {
        const date = document.createElement('small'); date.className = 'model-date';
        date.textContent = item.dating; date.title = item.dating; btn.append(date);
      }
      li.append(btn); return li;
    }));
  }
}
