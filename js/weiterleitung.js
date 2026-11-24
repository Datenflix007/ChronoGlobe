/* Startseite: Altlasten und QR-Links weiterleiten (aus index.html ausgelagert, damit die CSP keine Inline-Skripte braucht) */
  // Altlasten und QR-Links: index.html?vignetten=demo → Globus; index.html?code=XXXXXX → direkt beitreten
  (function () {
    var q = new URLSearchParams(location.search), lokal = q.get('sync') === 'lokal' ? '&sync=lokal' : '';
    if (q.get('vignetten')) location.replace('app.html?modus=frei&vignetten=' + encodeURIComponent(q.get('vignetten')));
    var c = (q.get('code') || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (c.length >= 4) location.replace('app.html?session=' + c + '&rolle=schueler' + lokal);
  })();
