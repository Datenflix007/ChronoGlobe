/* ChronoGlobe – Service Worker: Unterricht auch bei schwachem oder fehlendem WLAN.
   Angemeldet von js/offline.js (nur über https, also auf GitHub Pages, oder lokal mit ?sw=an).

   Strategien (nur Anfragen an die eigene Adresse; fremde Server – Supabase in Live-Sessions – gehen direkt ans Netz):
     HTML-Seiten         zuerst Netz, sonst Cache (neue Fassungen kommen sofort an)
     Kacheln img/tiles*  Cache, sonst Netz (Kacheln ändern sich praktisch nie)
     alles andere        sofort aus dem Cache, im Hintergrund aktualisieren („stale-while-revalidate“).
                         Versionierte Adressen (?v=<hash>, js/version.js) sind dadurch immer stimmig.
   Beim Installieren wird nur geladen, was der Start braucht (wie das Geräteprofil „niedrig“). Große Ebenen, Texturen und
   Kacheln kommen in den Cache, sobald sie einmal benutzt wurden – oder alle auf einmal über „Offline speichern“
   (Startseite, Nachricht 'alles-speichern').
   Datenschutz: Es wird nichts an Dritte gesendet; der Cache liegt nur im Browser des Geräts. */
importScripts('js/version.js');

var V = self.CG_VERSION, DATEN = 'cg-daten', KACHELN = 'cg-kacheln', KACHEL_MAX = 4000;
var SEITEN = ['./', 'index.html', 'app.html', 'quellen.html', 'lehrkraft.html', 'editor.html'];
// Bei Bedarf geladene große Dateien (js/app.js NACHLADEN, Netze, Quellenseite) und Texturen: nicht beim Installieren
var NICHT_START = /^(data\/(roemerstrassen|orbis_schiff|han_seidenstrasse|limes|sources|vignetten_demo)\.json|data\/netze\/(?!index\.json)|docs\/|img\/(?!icons\/favicon)|vendor\/supabase|tafelbilder\/.*\.(png|jpg|webp|md)$)/;

function adresse(pfad) { return new URL(pfad, self.registration.scope).href; }
function versioniert(pfad) { return adresse(self.cgUrl(pfad)); }
function speichern(cache, liste) {   // einzeln, damit eine fehlende Datei nicht alles abbricht
  return Promise.all(liste.map(function (u) {
    return fetch(u, { cache: 'no-cache' }).then(function (r) { if (r.ok) return cache.put(u, r); }).catch(function () {});
  }));
}

self.addEventListener('install', function (e) {
  var start = Object.keys(V.dateien).filter(function (p) { return !NICHT_START.test(p); }).map(versioniert);
  e.waitUntil(caches.open(DATEN).then(function (c) { return speichern(c, SEITEN.map(adresse).concat(start)); })
    .then(function () { return self.skipWaiting(); }));
});

/* Aufräumen: Einträge mit veraltetem ?v= entfernen, Kachel-Cache begrenzen */
self.addEventListener('activate', function (e) {
  e.waitUntil(Promise.all([
    caches.open(DATEN).then(function (c) {
      return c.keys().then(function (keys) {
        return Promise.all(keys.map(function (req) {
          var u = new URL(req.url), v = u.searchParams.get('v');
          if (!v) return null;
          var pfad = u.pathname.slice(new URL(self.registration.scope).pathname.length);
          return V.dateien[pfad] === v ? null : c.delete(req);
        }));
      });
    }),
    caches.open(KACHELN).then(function (c) {
      return c.keys().then(function (keys) {
        return Promise.all(keys.slice(0, Math.max(0, keys.length - KACHEL_MAX)).map(function (k) { return c.delete(k); }));
      });
    })
  ]).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var u = new URL(req.url);
  if (u.origin !== self.location.origin) return;   // fremde Server (Supabase) nie über den Cache
  var pfad = u.pathname.slice(new URL(self.registration.scope).pathname.length);

  if (req.mode === 'navigate' || /\.html$|\/$/.test(u.pathname)) {   // Seiten: Netz zuerst
    e.respondWith(fetch(req).then(function (r) {
      if (r.ok) { var k = r.clone(); caches.open(DATEN).then(function (c) { c.put(u.origin + u.pathname, k); }); }
      return r;
    }).catch(function () {
      return caches.open(DATEN).then(function (c) {
        return c.match(u.origin + u.pathname).then(function (hit) { return hit || c.match(adresse('index.html')); });
      });
    }));
    return;
  }

  if (/^img\/tiles(_schem)?\//.test(pfad)) {   // Kacheln: Cache zuerst
    e.respondWith(caches.open(KACHELN).then(function (c) {
      return c.match(req).then(function (hit) {
        return hit || fetch(req).then(function (r) { if (r.ok) c.put(req, r.clone()); return r; });
      });
    }));
    return;
  }

  // alles andere: sofort aus dem Cache, im Hintergrund erneuern
  e.respondWith(caches.open(DATEN).then(function (c) {
    return c.match(req).then(function (hit) {
      var netz = fetch(req).then(function (r) { if (r.ok) c.put(req, r.clone()); return r; });
      if (hit) { e.waitUntil(netz.catch(function () {})); return hit; }
      // offline und nicht exakt im Cache: dieselbe Datei mit anderer Versionsangabe nehmen (z. B. Texturen, die
      // die App ohne ?v= anfragt, „Offline speichern“ aber mit ?v= abgelegt hat)
      return netz.catch(function (err) {
        return c.match(req, { ignoreSearch: true }).then(function (alt) { if (alt) return alt; throw err; });
      });
    });
  }));
});

/* „Offline speichern“ (Startseite): alle Dateien aus js/version.js laden (Kacheln nicht: das wären über 100 MB;
   sie landen im Cache, sobald man in die Nahansicht zoomt). Fortschritt geht als Nachricht an die Seite zurück. */
self.addEventListener('message', function (e) {
  var d = e.data || {};
  if (d.art !== 'alles-speichern') return;
  var quelle = e.source, liste = Object.keys(V.dateien).map(versioniert), fertig = 0;
  var melden = function () { if (quelle) quelle.postMessage({ art: 'fortschritt', fertig: fertig, gesamt: liste.length }); };
  e.waitUntil(caches.open(DATEN).then(function (c) {
    var i = 0;
    function weiter() {   // vier gleichzeitig, damit das Schul-WLAN nicht verstopft
      if (i >= liste.length) return Promise.resolve();
      var u = liste[i++];
      return c.match(u).then(function (hit) {
        return hit || fetch(u).then(function (r) { if (r.ok) return c.put(u, r); });
      }).catch(function () {}).then(function () { fertig++; if (fertig % 5 === 0 || fertig === liste.length) melden(); return weiter(); });
    }
    return Promise.all([weiter(), weiter(), weiter(), weiter()]);
  }).then(function () { if (quelle) quelle.postMessage({ art: 'fertig', gesamt: liste.length }); }));
});
