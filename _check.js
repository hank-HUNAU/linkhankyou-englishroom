const fs=require('fs'),{execFileSync}=require('child_process');
function scripts(f){const s=fs.readFileSync(f,'utf8'),out=[];let re=/<script>([\s\S]*?)<\/script>/g,m;while(m=re.exec(s))out.push(m[1]);return out;}
const files=process.argv.slice(2);let fail=false;
files.forEach(f=>{
  if(f.endsWith('.js')){try{execFileSync('node',['--check',f],{stdio:'pipe'});console.log('OK  ',f);}catch(e){fail=true;console.log('FAIL',f,'\n'+String(e.stderr||e.message));}return;}
  scripts(f).forEach((b,i)=>{const t='_t_'+i+'.js';fs.writeFileSync(t,b);try{execFileSync('node',['--check',t],{stdio:'pipe'});console.log('OK  ',f,'s'+i);}catch(e){fail=true;console.log('FAIL',f,'s'+i,'\n'+String(e.stderr||e.message));}finally{fs.unlinkSync(t);}});
});
process.exit(fail?1:0);