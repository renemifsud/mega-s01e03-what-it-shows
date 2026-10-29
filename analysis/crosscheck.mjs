// Cross-check: run causes.ts logic (ported verbatim) + desk-notes split in Node with full ICU.
import fs from 'node:fs';
const D='kb/support-kb/src/lib/data/';
const raw=JSON.parse(fs.readFileSync(D+'reports-4471.json'));
const notes=JSON.parse(fs.readFileSync(D+'desk-notes.json'));
const tenants=new Map(fs.readdirSync(D+'tenants').map(f=>JSON.parse(fs.readFileSync(D+'tenants/'+f))).map(t=>[t.handle,t]));
const dayFirst=l=>{const o=new Intl.DateTimeFormat(l,{year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(Date.UTC(2026,0,2,12))).map(p=>p.type);return o.indexOf('day')<o.indexOf('month')};
const HINT={'booking-v2':'DD/MM/YYYY','booking-v3':'MM/DD/YYYY'};
const causeOf=(r,t)=>(!t||!dayFirst(t.locale))?null:(r.channel==='form'&&HINT[t.form].startsWith('MM')?'hint':'parser');
const uniq=[...new Map(raw.map(r=>[r.id,r])).values()].filter(r=>r.mergedInto===4471);
const desk={}, split={};
for(const r of uniq){const c=causeOf(r,tenants.get(r.tenant))??'unplaced';desk[c]=(desk[c]??0)+1;
  const p=notes.oneDayMove.includes(r.id)?'one-day':c; split[p]=(split[p]??0)+1;}
console.log('rows',raw.length,'unique merged',uniq.length);
console.log('desk CauseTable groups:',desk,' footnote one-day:',uniq.filter(r=>notes.oneDayMove.includes(r.id)).length);
console.log('split by real cause:',split);
// desk ref
const A='0123456789ABCDEFGHJKMNPQRSTVWXYZ';
const fnv=(s,seed)=>{let h=seed>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0}return h};
const deskRef=sig=>{const t=sig.trim();let bits=(BigInt(fnv(t,0x811c9dc5))<<8n)|BigInt(fnv(t,0x9e3779b9)&0xff);let o='';for(let i=0;i<8;i++){o=A[Number(bits&31n)]+o;bits>>=5n}return `DR-${o.slice(0,4)}-${o.slice(4)}`};
for(const s of ['René Mifsud','René Mifsud'.normalize('NFD'),'Rene Mifsud','renemifsud',' René Mifsud ']) console.log(JSON.stringify(s),s.length,deskRef(s));
