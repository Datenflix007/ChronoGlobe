/* ChronoGlobe: kleiner Markdown-Leser (aus js/app.js ausgelagert; genutzt für Lehrerhinweise und die Editor-Vorschau).
   Markdown.html(text)  → HTML: Überschriften, Absätze, Listen, Zitate, Tabellen, fett/kursiv/Code/Links.
   HTML im Text wird maskiert; Links nur zu http(s), relativen Pfaden und *.html (kein javascript:).
   Die erste Überschrift der Ebene 1 entfällt (den Titel trägt der Reiter). */
(function () {
  'use strict';
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  /* kleiner Markdown-Leser: Überschriften, Absätze, Listen, Zitate, Tabellen, fett/kursiv/Code/Links; HTML wird maskiert */
  function markdown(src) {
    var zeilen = src.replace(/\r/g, '').replace(/<!--[\s\S]*?-->/g, '').split('\n'), out = [], i = 0, ersteH1 = true;
    function inl(t) {
      return esc(t).replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<i>$2</i>')
        .replace(/\[([^\]]+)\]\(((?:https?:\/\/|\.{0,2}\/|[\w-]+\.html)[^)\s]*)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    }
    function zellen(z) { return z.trim().replace(/^\||\|$/g, '').split('|').map(function (c) { return c.trim(); }); }
    while (i < zeilen.length) {
      var z = zeilen[i], m;
      if (!z.trim()) { i++; continue; }
      if ((m = /^(#{1,4})\s+(.*)$/.exec(z))) {
        if (m[1].length === 1 && ersteH1) { ersteH1 = false; i++; continue; }   // Titel trägt der Reiter
        var h = Math.min(4, m[1].length + 1); out.push('<h' + h + '>' + inl(m[2]) + '</h' + h + '>'); i++; continue;
      }
      if (/^\s*\|/.test(z) && i + 1 < zeilen.length && /^\s*\|?\s*:?-{2,}/.test(zeilen[i + 1])) {
        var kopf = zellen(z), t = '<table class="ltab"><thead><tr>' + kopf.map(function (c) { return '<th>' + inl(c) + '</th>'; }).join('') + '</tr></thead><tbody>';
        i += 2;
        while (i < zeilen.length && /^\s*\|/.test(zeilen[i])) { t += '<tr>' + zellen(zeilen[i]).map(function (c) { return '<td>' + inl(c) + '</td>'; }).join('') + '</tr>'; i++; }
        out.push(t + '</tbody></table>'); continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(z)) {
        var ol = /^\s*\d+\./.test(z), li = [];
        while (i < zeilen.length && /^\s*([-*]|\d+\.)\s+/.test(zeilen[i])) { li.push('<li>' + inl(zeilen[i].replace(/^\s*([-*]|\d+\.)\s+/, '')) + '</li>'); i++; }
        out.push((ol ? '<ol>' : '<ul>') + li.join('') + (ol ? '</ol>' : '</ul>')); continue;
      }
      if (/^>\s?/.test(z)) {
        var q = [];
        while (i < zeilen.length && /^>\s?/.test(zeilen[i])) { q.push(zeilen[i].replace(/^>\s?/, '')); i++; }
        out.push('<blockquote>' + inl(q.join(' ')) + '</blockquote>'); continue;
      }
      var abs = [];
      while (i < zeilen.length && zeilen[i].trim() && !/^(#{1,4}\s|>|\s*\||\s*([-*]|\d+\.)\s)/.test(zeilen[i])) { abs.push(zeilen[i]); i++; }
      out.push('<p>' + inl(abs.join(' ')) + '</p>');
    }
    return out.join('\n');
  }
  window.Markdown = { html: markdown, esc: esc };
})();
