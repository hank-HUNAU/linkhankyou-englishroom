#!/usr/bin/env node
/**
 * 生成自签名证书（certs/key.pem + certs/cert.pem），用于本地/局域网 HTTPS。
 * 用法：node gen-cert.js
 * 生成后重启 server.js 会自动启用 HTTPS（加 --http 可强制回到 HTTP）。
 */
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const DIR = path.join(__dirname, 'certs');
const KEY = path.join(DIR, 'key.pem');
const CRT = path.join(DIR, 'cert.pem');

function findOpenssl(){
  const cands = [
    'openssl',
    'C:\\Program Files\\Git\\usr\\bin\\openssl.exe',
    'C:\\Program Files\\Git\\mingw64\\bin\\openssl.exe',
    'C:\\Program Files\\OpenSSL-Win64\\bin\\openssl.exe',
  ];
  for(const c of cands){
    const r = spawnSync(c, ['version'], { encoding:'utf8' });
    if(r.status === 0) return c;
  }
  return null;
}
function lanIPs(){
  const out = [];
  const ifs = os.networkInterfaces();
  for(const k of Object.keys(ifs)){
    for(const a of ifs[k] || []){
      if(a.family === 'IPv4' && !a.internal) out.push(a.address);
    }
  }
  return out;
}

const ossl = findOpenssl();
if(!ossl){
  console.error('未找到 openssl。请安装 OpenSSL，或手动把证书放到 certs/key.pem 与 certs/cert.pem。');
  process.exit(1);
}
fs.mkdirSync(DIR, { recursive: true });

const sans = ['DNS:localhost', 'IP:127.0.0.1', ...lanIPs().map(ip => 'IP:' + ip)].join(',');
const args = [
  'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '825',
  '-keyout', KEY, '-out', CRT,
  '-subj', '/CN=localhost',
  '-addext', 'subjectAltName=' + sans,
];
const r = spawnSync(ossl, args, {
  encoding: 'utf8',
  env: { ...process.env, MSYS2_ARG_CONV_EXCL: '*' },
});
if(r.status !== 0){
  console.error('生成失败：\n' + (r.stderr || r.stdout || ''));
  process.exit(1);
}
console.log('已生成证书：');
console.log('  私钥 ' + KEY);
console.log('  证书 ' + CRT);
console.log('  包含域名/IP：' + sans);
console.log('重启 server.js 即自动启用 HTTPS。浏览器首次访问会提示证书不受信任（自签名），选择"继续访问"即可。');