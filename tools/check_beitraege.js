/* Beiträge aus dem Editor prüfen (beitraege/*.json) und Themenebenen (data/ebenen/).
   Gleiche Regeln wie im Editor (js/themen.js). Läuft in der CI bei jedem Pull Request.

       node tools/check_beitraege.js
*/
'use strict';
const fs = require('fs'), path = require('path');
const Themen = require('../js/themen.js');
const ROOT = path.join(__dirname, '..');
let fehler = 0, geprueft = 0;

function lesen(rel) {
  try { return JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8')); }
  catch (e) { console.log('FEHLER ' + rel + ': kein gültiges JSON (' + e.message + ')'); fehler++; return null; }
}
function melden(rel, liste) {
  geprueft++;
  if (!liste.length) { console.log('ok     ' + rel); return; }
  fehler += liste.length;
  console.log('FEHLER ' + rel); liste.forEach(f => console.log('         – ' + f));
}

// 1. Beiträge
const ordner = path.join(ROOT, 'beitraege');
if (fs.existsSync(ordner)) fs.readdirSync(ordner).filter(n => n.endsWith('.json')).sort().forEach(n => {
  const rel = 'beitraege/' + n, b = lesen(rel); if (!b) return;
  const f = Themen.beitragPruefen(b);
  if (!/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.json$/.test(n)) f.push('Dateiname: JJJJ-MM-TT-titel.json (wie vom Editor erzeugt)');
  melden(rel, f);
});

// 2. Übernommene Themenebenen und ihr Register
const ix = lesen('data/ebenen/index.json');
if (ix) {
  if (!Array.isArray(ix.ebenen)) { console.log('FEHLER data/ebenen/index.json: "ebenen" muss eine Liste sein'); fehler++; }
  else ix.ebenen.forEach(m => {
    const f = [];
    if (!m.id || !m.name || !m.datei || !/^#[0-9a-fA-F]{6}$/.test(m.farbe || '')) f.push('Registereintrag braucht id, name, farbe, datei');
    const d = m.datei && fs.existsSync(path.join(ROOT, m.datei)) ? lesen(m.datei) : null;
    if (!d) f.push('Datei ' + m.datei + ' fehlt');
    else {
      Themen.ebenePruefen(d).forEach(x => f.push(x));
      if (d.id !== m.id) f.push('id im Register (' + m.id + ') und in der Datei (' + d.id + ') verschieden');
      const sp = Themen.spanne(d);
      if (m.von !== sp.von) f.push('von im Register sollte ' + sp.von + ' sein (frühestes Objekt)');
      if ((m.bis == null ? null : m.bis) !== sp.bis) f.push('bis im Register sollte ' + sp.bis + ' sein');
    }
    melden('data/ebenen/' + m.id, f);
  });
}

console.log('\n' + geprueft + ' geprüft, ' + fehler + ' Fehler');
process.exit(fehler ? 1 : 0);
