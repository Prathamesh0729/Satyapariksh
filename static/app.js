const form = document.getElementById('claimForm');
const headline = document.getElementById('headline');
const article = document.getElementById('article');
const sourceUrl = document.getElementById('sourceUrl');
const runBtn = document.getElementById('runBtn');
const emptyState = document.getElementById('emptyState');
const resultState = document.getElementById('resultState');
const verdict = document.getElementById('verdict');
const confidence = document.getElementById('confidence');
const realValue = document.getElementById('realValue');
const fakeValue = document.getElementById('fakeValue');
const realBar = document.getElementById('realBar');
const fakeBar = document.getElementById('fakeBar');
const modeLabel = document.getElementById('modeLabel');
const historyCount = document.getElementById('historyCount');
let scanMode = 'quick';

function getHistory(){try{return JSON.parse(localStorage.getItem('satyaHistory')||'[]')}catch{return[]}}
function saveHistory(item){const h=getHistory();h.unshift(item);localStorage.setItem('satyaHistory',JSON.stringify(h.slice(0,20)));historyCount.textContent=h.slice(0,20).length}
historyCount.textContent=getHistory().length;

document.querySelectorAll('.scan-tab').forEach(tab=>tab.addEventListener('click',()=>{
  document.querySelectorAll('.scan-tab').forEach(x=>x.classList.remove('active'));
  tab.classList.add('active');
  scanMode=tab.dataset.mode;
  modeLabel.textContent=scanMode==='deep'?'DEEP SCAN':'QUICK SCAN';
}));

form.addEventListener('submit',async(e)=>{
  e.preventDefault();
  const combined=[headline.value.trim(),article.value.trim()].filter(Boolean).join('\n\n');
  if(combined.length<20){alert('Please enter a claim or article with at least 20 characters.');return}
  runBtn.disabled=true;runBtn.innerHTML='Checking evidence… <span>↗</span>';
  try{
    const response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:combined,source_url:sourceUrl.value.trim(),mode:scanMode})});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'Analysis failed.');
    emptyState.classList.add('hidden');resultState.classList.remove('hidden');
    verdict.textContent=data.verdict;
    verdict.className='result-verdict '+data.verdict.toLowerCase();
    confidence.textContent=data.confidence+'%';
    realValue.textContent=data.real_probability+'%';fakeValue.textContent=data.fake_probability+'%';
    requestAnimationFrame(()=>{realBar.style.width=data.real_probability+'%';fakeBar.style.width=data.fake_probability+'%'});
    saveHistory({headline:headline.value.trim()||combined.slice(0,80),verdict:data.verdict,time:new Date().toISOString()});
  }catch(err){alert(err.message)}finally{runBtn.disabled=false;runBtn.innerHTML='Run the check <span>↗</span>'}
});

document.getElementById('newCheck').addEventListener('click',()=>{
  resultState.classList.add('hidden');emptyState.classList.remove('hidden');headline.focus();document.getElementById('detector').scrollIntoView({behavior:'smooth',block:'start'});
});

document.getElementById('historyBtn').addEventListener('click',()=>{
  const h=getHistory();
  if(!h.length){alert('No checks yet.');return}
  const text=h.slice(0,8).map((x,i)=>`${i+1}. ${x.verdict} — ${x.headline}`).join('\n');
  alert('Recent checks\n\n'+text);
});
