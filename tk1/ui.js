/* TH!NK · 统一图标系统（SVG sprite）
 * 用法：<script src="ui.js"></script> 放在页面内联脚本之前。
 *       JS 拼接：ICON('right')  →  <svg class="ico"><use href="#i-right"/></svg>
 *       静态标记：<svg class="ico"><use href="#i-right"/></svg>
 * 设计：24×24 网格，stroke=currentColor，随文字颜色/大小自适应（1em）。
 */
(function(){
  'use strict';
  var S = {
    left:        '<path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>',
    right:       '<path d="M5 12h14"/><path d="M12 5l7 7-7 7"/>',
    up:          '<path d="M12 19V5"/><path d="M5 12l7-7 7 7"/>',
    down:        '<path d="M12 5v14"/><path d="M19 12l-7 7-7-7"/>',
    play:        '<path d="M7 4.5v15l13-7.5z"/>',
    pause:       '<path d="M9 5v14"/><path d="M15 5v14"/>',
    check:       '<path d="M20 6L9 17l-5-5"/>',
    close:       '<path d="M18 6L6 18"/><path d="M6 6l12 12"/>',
    refresh:     '<path d="M20.5 12a8.5 8.5 0 1 1-2.5-6"/><path d="M20.5 3.5V9H15"/>',
    book:        '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    sound:       '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>',
    loop:        '<path d="M17 2l4 4-4 4"/><path d="M3 12V9a3 3 0 0 1 3-3h15"/><path d="M7 22l-4-4 4-4"/><path d="M21 12v3a3 3 0 0 1-3 3H3"/>',
    checkCircle: '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.2l2.4 2.4 4.6-4.8"/>',
    cap:         '<path d="M22 10L12 5 2 10l10 5z"/><path d="M6 12.2V17c0 1.2 2.7 2.6 6 2.6s6-1.4 6-2.6v-4.8"/>',
    teacher:     '<circle cx="12" cy="7.5" r="3.5"/><path d="M4.5 21v-1.2A7.5 7.5 0 0 1 12 12.3a7.5 7.5 0 0 1 7.5 7.5V21"/>',
    link:        '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    plus:        '<path d="M12 5v14"/><path d="M5 12h14"/>',
    trash:       '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>',
    warn:        '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4"/><path d="M12 17.2h.01"/>',
    search:      '<circle cx="11" cy="11" r="7.5"/><path d="M21 21l-4.5-4.5"/>',
    target:      '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".6"/>',
    clock:       '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.3l3.4 2"/>',
    chart:       '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',
    users:       '<circle cx="9" cy="8" r="3.4"/><path d="M2.5 20v-1a6.5 6.5 0 0 1 13 0v1"/><path d="M16.5 5.2a3.4 3.4 0 0 1 0 6.4"/><path d="M18 13.4A6.5 6.5 0 0 1 22 20v0"/>',
    star:        '<path d="M12 3.5l2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 10l6.1-.9z"/>',
    eye:         '<path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3.2"/>',
    edit:        '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3z"/><path d="M14.5 5.5l3 3"/>',
    mic:         '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0"/><path d="M12 17.5V21"/>',
    ear:         '<path d="M6 8.5a6 6 0 1 1 12 0c0 3-2 4-3.2 5.2-.9.9-1.3 1.6-1.3 2.6a2.5 2.5 0 0 1-5 0"/><path d="M10.5 9a1.8 1.8 0 0 1 3.5 0"/>',
    clipboard:   '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 12h6"/><path d="M9 16h4"/>',
    bulb:        '<path d="M9.5 18h5"/><path d="M10.5 21h3"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.3 1.1 2.2h5c.1-.9.5-1.7 1.1-2.2A6 6 0 0 0 12 3z"/>',
    logout:      '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    user:        '<circle cx="12" cy="8" r="3.6"/><path d="M5 20v-1a7 7 0 0 1 14 0v1"/>',
    calendar:    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M8 3v4"/><path d="M16 3v4"/>',
    inbox:       '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5.5L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.5A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8 1.5z"/>',
    folder:      '<path d="M3 7a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
  };
  var sprite = '<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true" focusable="false">';
  for (var k in S){ sprite += '<symbol id="i-' + k + '" viewBox="0 0 24 24">' + S[k] + '</symbol>'; }
  sprite += '</svg>';

  function mount(){
    if (document.getElementById('think-sprite')) return;
    var host = document.createElement('div');
    host.id = 'think-sprite';
    host.setAttribute('aria-hidden', 'true');
    host.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
    host.innerHTML = sprite;
    (document.body || document.documentElement).appendChild(host);
  }
  mount();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);

  function ICON(name, cls){
    return '<svg class="ico' + (cls ? ' ' + cls : '') + '" aria-hidden="true"><use href="#i-' + name + '"/></svg>';
  }
  window.ICON = ICON;
  window.THINK_ICONS = Object.keys(S);
})();