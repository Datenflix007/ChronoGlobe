(() => {
  'use strict';

  const searchInput = document.getElementById('quellenSuche');
  const categorySelect = document.getElementById('kategorieFilter');
  const results = document.getElementById('quellenListe');
  const counter = document.getElementById('treffer');
  const errorBox = document.getElementById('quelleFehler');
  const statusButtons = [...document.querySelectorAll('[data-status]')];

  const state = { query: '', category: 'all', status: 'all', registry: null };
  const normalise = (value) => String(value || '').toLocaleLowerCase('de-DE');
  const list = (value) => Array.isArray(value) ? value : [];

  // Anzeigenamen für source_type (Werte in data/sources.json bleiben englische Schlüssel)
  const TYPEN = {
    academic_publication: 'Fachpublikation',
    gis_dataset: 'GIS-Datensatz',
    project_reconstruction: 'Eigene Rekonstruktion',
    primary_source_dossier: 'Quellendossier',
    earth_imagery: 'Erdbild / Textur',
    reference_article: 'Nachschlageartikel',
    research_project: 'Forschungsprojekt',
    network_model: 'Netzwerkmodell',
    base_map: 'Basiskarte',
    reference_resource: 'Nachschlagewerk',
    publication_with_primary_sources: 'Publikation mit Quellenübersetzungen',
    primary_source_translation: 'Quellenübersetzung',
    primary_source: 'Primärquelle',
    research_archive: 'Forschungsarchiv',
    dataset_catalogue: 'Datensatzkatalog',
    gazetteer: 'Ortsverzeichnis (Gazetteer)'
  };

  function element(name, className, text) {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function externalLink(url, label) {
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) return null;
    const link = element('a', '', label || url);
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    return link;
  }

  function sourceText(source) {
    const period = source.historical_period || {};
    return normalise([
      source.title,
      source.institution,
      source.description,
      source.citation,
      source.doi,
      source.dataset_url,
      source.canonical_url,
      source.license && source.license.name,
      period.description,
      ...list(source.authors),
      ...list(source.geographic_scope),
      ...list(source.categories),
      ...list(source.used_by_layers).flatMap((layer) => [layer.id, layer.label, layer.description]),
      ...list(source.modifications),
      ...list(source.limitations)
    ].join(' '));
  }

  function appendDetailText(container, heading, value) {
    if (!value) return;
    const block = element('div', 'detailblock');
    block.append(element('strong', '', heading));
    block.append(element('p', '', value));
    container.append(block);
  }

  function appendDetailList(container, heading, items, formatter) {
    const values = list(items);
    if (!values.length) return;
    const block = element('div', 'detailblock');
    block.append(element('strong', '', heading));
    const ul = element('ul');
    values.forEach((item) => {
      const li = element('li');
      const rendered = formatter ? formatter(item) : item;
      if (rendered instanceof Node) li.append(rendered);
      else li.textContent = rendered;
      ul.append(li);
    });
    block.append(ul);
    container.append(block);
  }

  function addMeta(grid, label, value) {
    if (!value) return;
    const item = element('div');
    item.append(element('dt', '', label));
    item.append(element('dd', '', value));
    grid.append(item);
  }

  function buildCard(source, categoryNames, statusLabels) {
    const card = element('article', `quelle quelle-${source.usage_status}`);
    card.dataset.sourceId = source.id;

    const head = element('div', 'quelle-kopf');
    const titleBox = element('div');
    titleBox.append(element('h3', '', source.title || source.id));
    const authorLine = [list(source.authors).join(', '), source.publication_year].filter(Boolean).join(' · ');
    if (authorLine) titleBox.append(element('p', 'autor', authorLine));
    head.append(titleBox);
    head.append(element('span', `status status-${source.usage_status}`, statusLabels[source.usage_status] || source.usage_status));
    card.append(head);

    const badges = element('div', 'badges');
    list(source.categories).forEach((category) => {
      badges.append(element('span', 'badge', categoryNames.get(category) || category));
    });
    if (source.source_type) badges.append(element('span', 'badge', TYPEN[source.source_type] || source.source_type.replaceAll('_', ' ')));
    card.append(badges);

    if (source.description) card.append(element('p', 'beschreibung', source.description));

    const meta = element('dl', 'metadaten');
    const period = source.historical_period || {};
    addMeta(meta, 'Zeitraum', period.description || (period.start !== undefined || period.end !== undefined ? `${period.start ?? '?'} bis ${period.end ?? '?'}` : ''));
    addMeta(meta, 'Raum', list(source.geographic_scope).join(', '));
    addMeta(meta, 'Institution', source.institution);
    addMeta(meta, 'Version / Stand', source.version);
    const layers = list(source.used_by_layers).map((layer) => layer.label || layer.id).filter(Boolean).join(', ');
    addMeta(meta, 'Ebene in ChronoGlobe', layers);
    if (meta.children.length) card.append(meta);

    const details = element('details');
    details.append(element('summary', '', 'Nachweis, Ebenen und Hinweise'));
    const detailContent = element('div', 'detailinhalt');
    appendDetailText(detailContent, 'Statusgrundlage', source.status_basis);
    appendDetailText(detailContent, 'Bibliografische Angabe', source.citation);

    const links = [];
    if (source.doi) links.push({ url: `https://doi.org/${source.doi}`, label: `DOI: ${source.doi}` });
    if (source.dataset_url) links.push({ url: source.dataset_url, label: 'Datensatz / Download' });
    if (source.canonical_url) links.push({ url: source.canonical_url, label: 'Projekt- oder Quellenwebseite' });
    if (links.length) {
      const block = element('div', 'detailblock');
      block.append(element('strong', '', 'Verweise'));
      const ul = element('ul');
      links.forEach(({ url, label }) => {
        const link = externalLink(url, label);
        if (!link) return;
        const li = element('li');
        li.append(link);
        ul.append(li);
      });
      if (ul.children.length) {
        block.append(ul);
        detailContent.append(block);
      }
    }

    if (source.license && (source.license.name || source.license.note)) {
      const block = element('div', 'detailblock');
      block.append(element('strong', '', 'Lizenz / Nutzung'));
      const paragraph = element('p');
      const licenceLink = externalLink(source.license.url, source.license.name);
      if (licenceLink) paragraph.append(licenceLink);
      else if (source.license.name) paragraph.textContent = source.license.name;
      if (source.license.note) {
        paragraph.append(document.createTextNode(`${source.license.name ? ' — ' : ''}${source.license.note}`));
      }
      block.append(paragraph);
      detailContent.append(block);
    }

    appendDetailList(detailContent, 'Lokale Dateien und Rolle', source.local_files, (file) => {
      const fragment = document.createDocumentFragment();
      fragment.append(element('span', 'dateipfad', file.path || 'ohne Pfadangabe'));
      if (file.role) fragment.append(document.createTextNode(` — ${file.role}`));
      return fragment;
    });
    appendDetailList(detailContent, 'Bearbeitung in ChronoGlobe', source.modifications);
    appendDetailList(detailContent, 'Grenzen und Unsicherheiten', source.limitations);

    if (detailContent.children.length) {
      details.append(detailContent);
      card.append(details);
    }
    return card;
  }

  function render() {
    const registry = state.registry;
    if (!registry) return;
    const categoryNames = new Map(list(registry.categories).map((category) => [category.id, category.label]));
    const matches = list(registry.sources).filter((source) => {
      const statusMatches = state.status === 'all' || source.usage_status === state.status;
      const categoryMatches = state.category === 'all' || list(source.categories).includes(state.category);
      return statusMatches && categoryMatches && sourceText(source).includes(normalise(state.query));
    });

    results.replaceChildren();
    counter.textContent = `${matches.length} ${matches.length === 1 ? 'Eintrag' : 'Einträge'}`;
    results.setAttribute('aria-busy', 'false');
    if (!matches.length) {
      results.append(element('p', 'leer', 'Keine Einträge passen zu diesem Filter.'));
      return;
    }

    const grouped = new Map();
    matches.forEach((source) => {
      const category = source.primary_category || 'ohne-kategorie';
      if (!grouped.has(category)) grouped.set(category, []);
      grouped.get(category).push(source);
    });
    const orderedCategories = [
      ...list(registry.categories).map((category) => category.id),
      ...[...grouped.keys()].filter((id) => !categoryNames.has(id))
    ];
    orderedCategories.forEach((categoryId) => {
      const sources = grouped.get(categoryId);
      if (!sources || !sources.length) return;
      const section = element('section', 'kategorie-abschnitt');
      const heading = element('div', 'kategorie-kopf');
      heading.append(element('h2', '', categoryNames.get(categoryId) || 'Weitere Einträge'));
      heading.append(element('span', '', `${sources.length} ${sources.length === 1 ? 'Eintrag' : 'Einträge'}`));
      section.append(heading);
      const grid = element('div', 'kartenraster');
      sources.forEach((source) => grid.append(buildCard(source, categoryNames, registry.status_labels || {})));
      section.append(grid);
      results.append(section);
    });
  }

  function populateCategories(registry) {
    list(registry.categories).forEach((category) => {
      const option = element('option', '', category.label);
      option.value = category.id;
      categorySelect.append(option);
    });
  }

  function showStand(stand) {
    const box = document.getElementById('registerStand');
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(stand || '');
    if (!box || !match) return;
    box.textContent = `Stand des Registers: ${Number(match[3])}.${Number(match[2])}.${match[1]} · ${list(state.registry.sources).length} Einträge`;
    box.hidden = false;
  }

  function setStatus(status) {
    state.status = status;
    statusButtons.forEach((button) => {
      const active = button.dataset.status === status;
      button.classList.toggle('aktiv', active);
      button.setAttribute('aria-pressed', String(active));
    });
    render();
  }

  searchInput.addEventListener('input', () => {
    state.query = searchInput.value.trim();
    render();
  });
  categorySelect.addEventListener('change', () => {
    state.category = categorySelect.value;
    render();
  });
  statusButtons.forEach((button) => button.addEventListener('click', () => setStatus(button.dataset.status || 'all')));

  fetch('data/sources.json', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((registry) => {
      if (!registry || !Array.isArray(registry.sources) || !Array.isArray(registry.categories)) {
        throw new Error('Das Quellenregister hat nicht das erwartete Format.');
      }
      state.registry = registry;
      showStand(registry.stand);
      populateCategories(registry);
      render();
    })
    .catch((error) => {
      results.setAttribute('aria-busy', 'false');
      counter.textContent = 'Register nicht verfügbar';
      errorBox.hidden = false;
      errorBox.textContent = `Das Quellenregister konnte nicht geladen werden (${error.message}).`;
    });
})();
