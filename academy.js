'use strict';
(() => {
  // Single source of truth: the same TXT that visitors can download.
  let raw='';
  let chapters=[];
  const englishTitles=["Purpose of the Academy","Ethics and values first","Eight moral principles","Dignity, freedom and dispute resolution","How Omnia-Mundi works","Mandatory common preparation","Customer","Procurer","Manufacturer","Seller","Receiver common program","Receiver Home","Receiver Warehouse","Receiver Store","Moderator common program","Sender Curator","Receiver Curator","Order Supervisor","Administrator","Business Connections","Free Goods and charity","Logistics and returns","Finance, prices and documents","International trade and law","Communication and conflict","Teaching format","Knowledge assessment and authorization","Specialized training","Mistakes, retraining and appeals","Teachers and assessors","Digital learning account","Quality assurance and updates","Academy development stages","Practical case studies","Glossary","Launch readiness","Ethics before professional duties"];
  const nav=document.getElementById('academy-nav'),body=document.getElementById('academy-body');
  const trans=(key,defaultText)=>{try{return window.OmniaI18n.t(key)}catch{return defaultText}};
  function contentFragment(text){
    const frag=document.createDocumentFragment();
    for(const block of text.trim().split(/\n\s*\n/)){
      const lines=block.split('\n').map(s=>s.trim()).filter(s=>s&&!/^={8,}$/.test(s));if(!lines.length)continue;
      if(lines.length===1&&lines[0].length<140&&/^[А-ЯЁA-Z0-9 ,.:—()«»\-]+$/.test(lines[0])){const h=document.createElement('h3');h.textContent=lines[0];frag.append(h);continue;}
      const hasBullets=lines.some(x=>x.startsWith('- '));
      if(!hasBullets){const p=document.createElement('p');p.textContent=lines.join(' ');frag.append(p);continue;}
      let paragraph=[],list=null;const flush=()=>{if(paragraph.length){const p=document.createElement('p');p.textContent=paragraph.join(' ');frag.append(p);paragraph=[];}};
      for(const line of lines){if(line.startsWith('- ')){flush();if(!list){list=document.createElement('ul');frag.append(list);}const li=document.createElement('li');li.textContent=line.slice(2);list.append(li);}
      else if(list&&list.lastElementChild){list.lastElementChild.textContent+=' '+line;}
      else paragraph.push(line);}flush();
    }
    return frag;
  }
  function draw(){
    body.replaceChildren();nav.replaceChildren();
    const en=new URL(location.href).searchParams.get('lang')==='en'||document.documentElement.lang==='en';
    const intro=raw.slice(0,chapters[0].index).split(/={20,}/)[0].trim();
    const note=document.createElement('p');note.className='academy-original';note.textContent=intro.replace(/\n/g,' · ');body.append(note);
    chapters.forEach((m,i)=>{
      const id='chapter-'+String(i+1).padStart(2,'0'),end=chapters[i+1]?.index??raw.length;
      const article=document.createElement('section');article.id=id;article.className='academy-chapter';
      const h=document.createElement('h2');const n=document.createElement('span');n.textContent=String(i+1).padStart(2,'0');
      h.append(n,document.createTextNode(en?englishTitles[i]:m[1].replace(/^\d{2}\. /,'')));article.append(h);
      article.append(contentFragment(raw.slice(m.index+m[0].length,end)));
      const up=document.createElement('a');up.href='#academy-toc';up.className='up';up.textContent=trans('academy.up','К оглавлению');article.append(up);body.append(article);
      const a=document.createElement('a');a.href='#'+id;const num=document.createElement('b');num.textContent=String(i+1).padStart(2,'0');a.append(num,document.createTextNode(en?englishTitles[i]:m[1].replace(/^\d{2}\. /,'')));nav.append(a);
    });
  }
  // The program is loaded once; changing the interface language only re-renders it.
  if(window.OmniaI18n?.subscribe)window.OmniaI18n.subscribe(()=>{if(chapters.length)draw();});
  async function loadProgram(){
    try{
      const response=await fetch('academy-program-ru.txt',{cache:'no-cache'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      const text=await response.text();
      const matches=[...text.matchAll(/^={50,}\n(\d{2}\. [^\n]+)\n={50,}\n/gm)];
      if(matches.length!==37)throw new Error('Unexpected program structure: '+matches.length);
      raw=text;chapters=matches;
      draw();
    }catch(error){
      console.error('Could not load Academy source document:',error);
      const notice=document.createElement('p');
      notice.setAttribute('role','alert');
      notice.setAttribute('data-i18n','academy.loadError');
      notice.textContent=trans('academy.loadError','Не удалось загрузить программу. Скачайте TXT-файл по ссылке выше.');
      body.replaceChildren(notice);
    }
  }
  loadProgram();
})();