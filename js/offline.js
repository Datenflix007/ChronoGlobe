/* ChronoGlobe: Service Worker (sw.js) anmelden und „Offline speichern“ anbieten.
   Angemeldet wird nur über https (GitHub Pages). Lokal (http://localhost, Tests) bleibt alles wie bisher, außer mit
   ?sw=an in der Adresse. ?sw=aus meldet einen vorhandenen Service Worker ab und leert seine Caches.
   Ein Element mit id="offlineKnopf" (Startseite) wird zum Knopf „Für den Unterricht offline speichern“. */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator)) return;
  var q = new URLSearchParams(location.search).get('sw');
  if (q === 'aus') {
    navigator.serviceWorker.getRegistrations().then(function (l) { l.forEach(function (r) { r.unregister(); }); });
    if (window.caches) caches.keys().then(function (k) { k.filter(function (n) { return /^cg-/.test(n); }).forEach(function (n) { caches.delete(n); }); });
    return;
  }
  if (location.protocol !== 'https:' && q !== 'an') return;

  var anmeldung = navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).catch(function (e) { console.warn('Service Worker:', e); return null; });

  function knopfEinrichten() {
    var k = document.getElementById('offlineKnopf'); if (!k) return;
    k.hidden = false;
    var text = k.textContent;
    k.addEventListener('click', function () {
      k.disabled = true; k.textContent = 'Wird gespeichert …';
      anmeldung.then(function () { return navigator.serviceWorker.ready; }).then(function (r) {
        navigator.serviceWorker.addEventListener('message', function hoeren(e) {
          var d = e.data || {};
          if (d.art === 'fortschritt') k.textContent = 'Wird gespeichert … ' + Math.round(d.fertig / d.gesamt * 100) + ' %';
          if (d.art === 'fertig') {
            navigator.serviceWorker.removeEventListener('message', hoeren);
            k.textContent = '✓ Offline gespeichert (' + d.gesamt + ' Dateien; Nahansicht-Kacheln nur, wo schon besucht)';
            if (navigator.storage && navigator.storage.persist) navigator.storage.persist();   // Browser bitten, den Cache nicht zu räumen
          }
        });
        r.active.postMessage({ art: 'alles-speichern' });
      }).catch(function () { k.disabled = false; k.textContent = text + ' (fehlgeschlagen, bitte erneut versuchen)'; });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', knopfEinrichten); else knopfEinrichten();
})();
