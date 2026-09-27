/* TH!NK 存储垫层：让 localStorage 变为「云同步」。
   原理：登录后先把服务端数据水合进本地 → 各页面引擎照常同步读；
   任何 setItem/removeItem 都会被镜像到服务端（按登录用户分桶），跨设备互通。 */
(function(){
  /* 直开文件（file://）会连不上后端 → 直接给出正确打开方式的指引 */
  if(location.protocol === 'file:'){
    var d=document.createElement('div');
    d.style.cssText='position:fixed;inset:0;z-index:2147483647;background:#10122b;color:#fff;display:flex;align-items:center;justify-content:center;padding:28px;font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;';
    d.innerHTML='<div style="max-width:560px;line-height:1.75">'+
      '<h2 style="margin:0 0 12px;font-size:22px;">不要直接双击 HTML 文件</h2>'+
      '<p style="margin:0 0 12px;color:#cbd5e1;">这是一个带后端服务的应用，须通过服务器访问，否则无法登录与同步数据。</p>'+
      '<ol style="margin:0 0 14px;padding-left:20px;color:#e2e8f0;display:grid;gap:6px;">'+
      '<li>打开终端（PowerShell / CMD），进入本目录：<br><code style="background:#ffffff24;padding:2px 8px;border-radius:6px;font-size:13px;">cd xueersi-diancan-原型</code></li>'+
      '<li>启动服务：<br><code style="background:#ffffff24;padding:2px 8px;border-radius:6px;font-size:13px;">node server.js</code></li>'+
      '<li>用浏览器打开（别用双击）：<br><code style="background:#10B98133;border:1px solid #10B981;padding:2px 8px;border-radius:6px;font-size:13px;color:#34d399;">http://localhost:8000/教师端.html</code></li>'+
      '</ol>'+
      '<button style="cursor:pointer;background:#10B981;color:#032a1d;border:none;font-weight:800;font-size:14px;padding:9px 16px;border-radius:10px;">我已用服务器打开，关闭提示</button></div>';
    var btn=d.querySelector('button'); btn.onclick=function(){ d.remove(); };
    (document.body||document.documentElement).appendChild(d);
    return;
  }

  var TOK='tf_token', USER='tf_user';
  var token = localStorage.getItem(TOK);
  var user=null; try{ user = JSON.parse(localStorage.getItem(USER)); }catch(e){}

  function api(path, opts){
    return fetch('/api'+path, Object.assign({
      headers: Object.assign({}, (opts||{}).headers || {}, token ? { 'Authorization':'Bearer '+token } : {}),
      cache:'no-store'
    }, opts)).then(function(r){ return r.json().catch(function(){ return {}; }); });
  }

  /* 教师/助教发的任务需全局可见（学生也能读到）；其余按本人分桶 */
  function scopeFor(k){
    if(!user) return '';
    return ((user.role==='teacher' || user.role==='assistant') && k==='tf_assignments') ? 'global' : '';
  }

  /* 逐项水合 */
  function hydrate(){
    if(!token) return 'guest';
    api('/kv').then(function(res){
      if(res && res.rows){
        Object.keys(res.rows).forEach(function(k){ try{ localStorage.setItem(k, res.rows[k]); }catch(e){} });
      }
      window.dispatchEvent(new Event('store-hydrated'));
    }).catch(function(){});
  }

  /* 写入镜像：积累 → debounce → 批量 POST */
  var queue=[], timer=null;
  function schedule(){
    if(timer) return;
    timer=setTimeout(flush, 500);
  }
  function flush(){
    timer=null;
    if(!token){ queue.length=0; return; }
    if(!queue.length) return;
    var batch = queue; queue=[];
    api('/kv', { method:'POST', body: JSON.stringify(batch) }).catch(function(){});
  }

  var _set  = Storage.prototype.setItem;
  var _rm   = Storage.prototype.removeItem;
  Storage.prototype.setItem = function(k,v){
    _set.call(this,k,v);
    queue.push({ op:'set', key:k, value:v, scope:scopeFor(k) });
    schedule();
  };
  Storage.prototype.removeItem = function(k){
    _rm.call(this,k);
    queue.push({ op:'del', key:k, scope:scopeFor(k) });
    schedule();
  };

  window.storeMeta = { token:token, user:user, api:api, hydrate:hydrate };
  hydrate();
})();