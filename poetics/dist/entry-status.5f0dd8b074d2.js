'use strict';
(function(){
const validDate=s=>/^\d{4}-\d{2}-\d{2}$/.test(s||'')&&!Number.isNaN(Date.parse(s+'T12:00:00Z'))&&new Date(s+'T12:00:00Z').toISOString().slice(0,10)===s;
function classify(record,now=new Date()){
 const today=now.toISOString().slice(0,10),cutoff=new Date(now);cutoff.setUTCFullYear(cutoff.getUTCFullYear()-1);const since=cutoff.toISOString().slice(0,10);
 const qualified=x=>x&&x.url&&/^https?:\/\//.test(x.url)&&validDate(x.date);
 if(!['Platforms','Prizes'].includes(record.category))return null;
 const closure=record.closure;if(qualified(closure)&&closure.date<=today)return {label:'Inactive — confirmed',date:closure.date,url:closure.url,note:closure.note||'Explicit closure or suspension announcement.'};
 if(record.oneOff&&record.phase?.label==='Completed'&&qualified(record.phase))return {label:'Historical',date:record.phase.date,url:record.phase.url,note:'Completed one-off event; no claim of a continuing series.'};
 const evidence=(record.activities||[]).filter(x=>qualified(x)&&['held event','programme announcement','call','award','publication'].includes(x.kind)&&x.date>=since&&x.date<=today).sort((a,b)=>b.date.localeCompare(a.date))[0];
 if(evidence)return {label:'Active',date:evidence.date,url:evidence.url,note:evidence.basis||'Documented organising or programme activity within the past 12 months.'};
 const upcoming=record.upcoming;if(qualified(upcoming)&&upcoming.confirmed===true&&upcoming.date>=today&&(!upcoming.reviewBy||upcoming.reviewBy>=today))return {label:'Active',date:upcoming.date,url:upcoming.url,note:'Confirmed upcoming edition; occurrence not yet established.'};
 if(record.historical===true&&record.verification?.sourceURL)return {label:'Historical',date:record.phase?.date||null,url:record.verification.sourceURL,note:'Documented historical initiative; current operation not claimed.'};
 return {label:'Status unverified',date:null,url:null,note:'Recent activity has not been established. Older evidence and silence do not mean inactive.'};
}
window.PoeticsEntryStatus={classify,validDate};
})();
