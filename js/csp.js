/* ChronoGlobe: Content-Security-Policy – setzt die Datenschutzregel technisch durch (CLAUDE.md, Regel 6).
   Steht als erstes Skript im <head> jeder Seite und fügt das <meta http-equiv="Content-Security-Policy"> ein.
   (GitHub Pages kann keine eigenen HTTP-Kopfzeilen senden; als Meta-Element gilt die Richtlinie ab dem Einfügen.)

   Freier Modus, Tafelbilder, Quellen- und Lehrkraftseite: Verbindungen nur zur eigenen Adresse.
   Live-Sessions (app.html?session=…) und Startseite (legt Sessions an, tritt bei): zusätzlich Supabase.
   Wer Supabase unter einer eigenen Domain betreibt, trägt sie unten in SUPABASE ein. */
(function () {
  'use strict';
  var SUPABASE = 'https://*.supabase.co wss://*.supabase.co';
  var seite = location.pathname.split('/').pop() || 'index.html';
  var mitSession = /[?&]session=/.test(location.search) || seite === 'index.html';
  var regeln = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",              // style-Attribute in app.html und in erzeugtem HTML
    "img-src 'self' data: blob:",                    // 'data:,' = „keine Kachel“, QR-Code als Bild
    "font-src 'self'",
    "connect-src 'self' data: blob:" + (mitSession ? ' ' + SUPABASE : ''),
    "worker-src 'self' blob:",                       // sw.js; three.js/globe.gl erzeugen Worker aus blob:
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ];
  var m = document.createElement('meta');
  m.httpEquiv = 'Content-Security-Policy';
  m.content = regeln.join('; ');
  document.head.appendChild(m);
})();
