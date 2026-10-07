"""Reproduce auger powder flowability summary. Run from /workspace with python analysis/analysis.py.
Inputs: supplied README_EDISON.md, data/battery, data/opt and powder-properties.
Outputs: analysis/*.csv, analysis/*.png, analysis/*.pdf.
All screening metrics are exploratory; no LPBF spreading outcome measurements are available.
"""
# --- Executed notebook block 3 ---
import os
for root,dirs,files in os.walk('/workspace'):
 if root.count(os.sep)>3: dirs[:]=[]; continue
 print(root,[(f,round(os.path.getsize(os.path.join(root,f))/1024,1)) for f in files[:30]])

# --- Executed notebook block 4 ---
import glob,pandas as pd, json,numpy as np
for pattern in ['/workspace/data/battery/*','/workspace/data/opt/*']:
 a=glob.glob(pattern);print(pattern,len(a),[(os.path.basename(x),len(glob.glob(x+'/**/*',recursive=True))) for x in a[:30]])
for p in ['/workspace/docs/battery-runs/run-log.csv','/workspace/data/powder-properties/battery_responses.csv','/workspace/data/powder-properties/literature_powder_properties.csv']:
 d=pd.read_csv(p);print('\n',p,d.shape,list(d.columns));print(d.head(3).to_string(index=False)[:2400])

log=pd.read_csv('/workspace/docs/battery-runs/run-log.csv')

# --- Executed notebook block 10 ---
from scipy import stats, optimize, signal
from pathlib import Path
out=Path('/workspace/analysis');out.mkdir(exist_ok=True)
valid=log[(log.qc_valid==True)&log.blocks.fillna('').str.contains('A')].copy();records=[];polls=[]
for _,r in valid.iterrows():
 base=Path('/workspace')/r.data_dir; tf=list(base.glob('trials_*.csv'));pf=list(base.glob('polls_*.csv'))
 if not tf:continue
 d=pd.read_csv(tf[0]);d['run']=base.name;d['powder']=r.powder_id;d['date']=r.started_utc[:10];records.append(d)
 if pf:
  p=pd.read_csv(pf[0]);p['run']=base.name;p['powder']=r.powder_id;polls.append(p)
t=pd.concat(records,ignore_index=True);pol=pd.concat(polls,ignore_index=True)
A=t.query('block=="A"');C=t.query('block=="C"');D=t.query('block=="D"');B=t.query('block=="B"');E=t.query('block=="E"');
print('A',A.shape,'C',C.shape,'D',D.shape,'pol D',pol.query('block=="D"').shape)
print('A metrics',A[['delta_g','sigma_g','drift_g','shock_g']].describe(percentiles=[.5,.9,.95]).round(4).to_string());print('nonzero shocks',t.groupby('block').shock_g.apply(lambda s:(s.fillna(0)!=0).sum()).to_string(), 'retries',t.groupby('block').retries.sum().to_string())
cs=C.groupby(['run','powder','tilt_deg']).delta_g.agg(['mean','std','count']).reset_index();cs['cv']=cs['std']/cs['mean'];print('\nC summary valid >noise mean > 0.01 g');print(cs.groupby('tilt_deg').cv.agg(['median','mean','min','max','count']).to_string()); print('\nsalt',cs.query('powder=="salt"').to_string(index=False))
print('\nqual',C.quality.value_counts());print('pol D',pol.query('block=="D"').groupby(['run','rpm']).size().describe())

# --- Executed notebook block 12 ---
ss=[]
for p in glob.glob('/workspace/data/opt/salt*/zero/trial_*.json'):
 j=json.load(open(p));x=j.get('parameters_executed') or {};ss.append({'idx':j['trial_index'],'tilt':x.get('bulk_tilt_deg'),'rpm':x.get('bulk_rpm'),'tap':x.get('bulk_tap'),'time':j['outcomes'].get('t_bulk_s'),'n':len(j['telemetry']['rows']),'stop':j['stop_events'][0] if j['stop_events'] else None,'p':p})
sdf=pd.DataFrame(ss).sort_values('idx');print(sdf[['idx','tilt','rpm','tap','time','n']].to_string(index=False));print('counts same settings',sdf.groupby(['tilt','rpm','tap'],dropna=False).size().sort_values(ascending=False).head(20).to_string())

# --- Executed notebook block 15 ---
# Choice: exclude 08-06 salt from stable repeatability because under-filled auger (curated source notes).
cc=cs[~cs.run.str.contains('20260806T145120Z')]; conveying=['salt','white-rice-flour','sodium-alginate','calcium-lactate','carboxymethyl-cellulose','xanthan-gum','sodium-sulfate','silicon-110-200','alsi10mg','barium-chloride']
cc2=cc[cc.powder.isin(conveying)];print('C CV by tilt all conveying',cc2.groupby('tilt_deg').cv.agg(['median','mean','count']).round(3).to_string());print('C CV Al',cc2.query('powder=="alsi10mg"').to_string(index=False));
ssalt=cc2.query('powder=="salt"');
for a,g in ssalt.groupby('tilt_deg'):
 print('salt',a,'mean mg',g['mean'].mean()*1000,'between CV %',g['mean'].std(ddof=1)/g['mean'].mean()*100,'within pooled CV %',np.sqrt(np.mean(g['std']**2))/g['mean'].mean()*100)
dd=D.assign(ff_gpr=lambda x:x.delta_g/3)
match=dd[dd.rpm==45].merge(cs[cs.tilt_deg==45][['run','mean']],on='run');match['ratio']=match.ff_gpr/match['mean'];print('D45/C45 ratios',match[['powder','ratio']].round(2).to_string(index=False))

# --- Executed notebook block 16 ---
def readtele(j):
 h=j['telemetry']['header'];rows=j['telemetry']['rows'];
 if not h or not rows:return pd.DataFrame()
 from io import StringIO
 return pd.read_csv(StringIO(h+'\n'+'\n'.join(rows)))
# Remove D first / last? include all movement but polls may include pause, use trials t_ms endpoint and start 3*60/rpm before it.
sl=[];ims=[]
for (run,rpm),g in pol.query('block=="D"').groupby(['run','rpm']):
 g=g.sort_values('t_ms'); d=dd[(dd.run==run)&(dd.rpm==rpm)].iloc[0];end=d.t_ms;start=end-3*60000/rpm
 z=g[(g.t_ms>=start-800)&(g.t_ms<=end+800)].copy()
 # trim to movement duration; best avoids included idle intervals, but motion timing in firmware asynchronous start may have lag
 z=z[(z.t_ms>=start)&(z.t_ms<=end)]
 if len(z)<4:continue
 x=(z.t_ms-z.t_ms.min())/1000;y=z.grams.to_numpy();fit=stats.linregress(x,y)
 sl.append(dict(run=run,powder=d.powder,rpm=rpm,n=len(z),seg_s=x.max(),poll_ff=fit.slope*60/rpm,endpoint_ff=d.ff_gpr,r2=fit.rvalue**2,rmse=np.std(y-fit.intercept-fit.slope*x,ddof=2)))
 if rpm==15:
  q=z.copy();dt=np.diff(q.t_ms)/1000;rate=np.diff(q.grams)/dt;positive=np.maximum(rate,0)
  # noise threshold: 2 mg accumulated in >=0.3s; none below noise floor interpret only high feed traces
  mu=np.median(rate); mrate=stats.median_abs_deviation(rate,scale='normal')/abs(mu) if mu>0 else np.nan
  zero=(rate<0.002/dt).mean()
  # quantify priming delay after prior C: threshold 5mg
  prim=((q.t_ms.iloc[np.flatnonzero(q.grams.to_numpy()-q.grams.iloc[0]>0.005)[0]]-q.t_ms.iloc[0])/1000 if (q.grams.to_numpy()-q.grams.iloc[0]>0.005).any() else np.nan)
  ims.append(dict(run=run,powder=d.powder,rate_mad=mrate,zero_frac=zero,prim_s=prim))
slope=pd.DataFrame(sl);inter=pd.DataFrame(ims)
print('slope',slope.shape, slope.groupby('rpm')[['r2','poll_ff','endpoint_ff','rmse']].median().round(4).to_string());print('slope sample',slope.query('powder=="salt"').round(4).to_string(index=False));print('inter',inter.round(2).to_string(index=False))

# --- Executed notebook block 18 ---
sl=[]; ims=[]
for (run,rpm),g in pol.query('block=="D"').groupby(['run','rpm']):
 g=g.sort_values('t_ms');d=dd[(dd.run==run)&(dd.rpm==rpm)].iloc[0]
 x=(g.t_ms-g.t_ms.min())/1000; y=g.grams.to_numpy();fit=stats.linregress(x,y)
 sl.append(dict(run=run,powder=d.powder,rpm=rpm,n=len(g),seg_s=x.max(),poll_ff=fit.slope*60/rpm,endpoint_ff=d.ff_gpr,r2=fit.rvalue**2,rmse=np.std(y-fit.intercept-fit.slope*x,ddof=2)))
 if rpm==15:
  dt=np.diff(g.t_ms)/1000;rate=np.diff(g.grams)/dt;mu=fit.slope
  # noise: single-poll negative rates not meaningful at < 10 mg/rev
  mad=stats.median_abs_deviation(rate,scale='normal')/mu if mu>0.002 else np.nan
  zf=(rate<.002/dt).mean() if mu>0.002 else np.nan
  prim=((g.t_ms.iloc[np.flatnonzero(y-y[0]>.005)[0]]-g.t_ms.iloc[0])/1000 if (y-y[0]>.005).any() else np.nan)
  # spectral at f_rev using 15rpm trace; interpolate to uniform grid before periodogram
  if mu>.002 and len(g)>20:
   xu=np.arange(0,x.max(),np.median(dt));ru=np.interp(xu,x[:-1]+dt/2,rate);freq,px=signal.periodogram(ru-ru.mean(),fs=1/np.median(dt));band=(freq>=.15)&(freq<=1.5);peak=np.abs(freq-.25).argmin();peakshare=px[peak]/px[band].sum() if px[band].sum()>0 else np.nan
  else:peakshare=np.nan
  ims.append(dict(run=run,powder=d.powder,rate_mad=mad,zero_frac=zf,prim_s=prim,rev_power=peakshare))
slope=pd.DataFrame(sl);inter=pd.DataFrame(ims)
print('slope n',len(slope),'medians',slope.groupby('rpm')[['r2','rmse']].median().round(4).to_string());print('ratio slope to endpoint',slope.assign(r=lambda z:z.poll_ff/z.endpoint_ff).groupby('rpm').r.agg(['median','count']).to_string());print(inter.round(3).to_string(index=False))

# --- Executed notebook block 20 ---
props=pd.read_csv('/workspace/data/powder-properties/literature_powder_properties.csv').set_index('powder_id')
feat=[]
for name in props.index:
 g=cc2[cc2.powder==name];
 if not len(g):continue
 vals={int(a):h['mean'].mean()*1000 for a,h in g.groupby('tilt_deg')}; cvs={int(a):h.cv.median() for a,h in g.groupby('tilt_deg')}
 dr=dd[(dd.powder==name)&(~dd.run.str.contains('20260806T145120Z'))]; ds=dr.groupby('rpm').ff_gpr.mean();
 it=inter[(inter.powder==name)&(~inter.run.str.contains('20260806T145120Z'))]
 et=E[(E.powder==name)&(E.phase=='tap')&(E.tilt_deg==45)&(~E.run.str.contains('20260806T145120Z'))]
 # use only taps whose quality not unsettled/shock; readings from early runs without QC annotation assessed cautiously
 tap=et.delta_g.median()*1000 if len(et) and not (et.quality=='shock').all() else np.nan
 bh=B[(B.powder==name)&(B.tilt_deg==90)&(~B.run.str.contains('20260806T145120Z'))];bh=bh[~bh.quality.isin(['shock','unsettled'])]
 feat.append(dict(powder=name,ff0=vals.get(0,np.nan),ff45=vals.get(45,np.nan),ff90=vals.get(90,np.nan),vol90=vals.get(90,np.nan)/props.loc[name,'bulk_density_g_ml'],gain=vals.get(90,np.nan)/vals.get(0,np.nan) if vals.get(0,0)>3 else np.nan,gain45=vals.get(45,np.nan)/vals.get(0,np.nan) if vals.get(0,0)>3 else np.nan,cv0=cvs.get(0),cv45=cvs.get(45),cv90=cvs.get(90),speed=(ds.get(90,np.nan)/ds.get(15,np.nan)-1)*100 if ds.get(15,0)>.01 else np.nan,zero=it.zero_frac.median(),mad=it.rate_mad.median(),prim=it.prim_s.median(),period=it.rev_power.median(),tap=tap,hold90=bh.delta_g.mean()*1000 if len(bh) else np.nan,angle=props.loc[name,'angle_repose_deg'],hr=props.loc[name,'hausner_ratio']))
f=pd.DataFrame(feat).set_index('powder');print(f.round(2).to_string());f.to_csv(out/'feature_table.csv')
cols=['ff0','ff45','ff90','vol90','gain','gain45','cv0','cv45','cv90','speed','zero','mad','prim','period','tap','hold90']
cor=[]
for col in cols:
 for target in ['angle','hr','vol90','zero']:
  if col==target:continue
  z=f[[col,target]].replace([np.inf,-np.inf],np.nan).dropna();rho,p=stats.spearmanr(z[col],z[target]) if len(z)>3 and z[col].nunique()>1 and z[target].nunique()>1 else (np.nan,np.nan)
  cor.append(dict(feature=col,target=target,n=len(z),rho=rho,p=p))
cors=pd.DataFrame(cor);print('\nAoR /HR');print(cors.query('target in ["angle","hr"]').pivot(index='feature',columns='target',values=['n','rho']).round(2).to_string());cors.to_csv(out/'correlations.csv',index=False)
print('\nmutual');print(cors.query('target in ["vol90","zero"]').pivot(index='feature',columns='target',values='rho').round(2).to_string())

# --- Executed notebook block 24 ---
files={}
for p in glob.glob('/workspace/data/opt/production-*/zero/trial_*.json'):
 j=json.load(open(p));z=readtele(j)
 if len(z):files['alsi' if 'alsi10mg' in p else Path(p).stem.split('_')[1][:8]]=z
print(files.keys())
def win_rates(z, lo,hi, w=2):
 b=z[z.phase=='bulk'].dropna(subset=['m_g','t_s']);b=b[(b.t_s>=lo)&(b.t_s<=hi)]
 # interpolation on 2s evenly spaced bins
 if len(b)<5:return np.array([])
 grid=np.arange(lo,hi+.001,w);return np.diff(np.interp(grid,b.t_s,b.m_g))/w
for key,z in files.items():
 if key=='alsi': a,b=29,58
 elif key=='de4dd913':a,b=8,35
 else:a,b=7,26
 q=win_rates(z,a,b);print(key,'interval',a,b,'nwin',len(q),'mean g/s',q.mean(),'median',np.median(q),'CV',q.std(ddof=1)/q.mean(),'zero <1mg/s', (q<.001).mean(),'negative',sum(q<0),'rate q10/90',np.quantile(q,[.1,.9])); print('time subsets',(z.phase=='bulk').sum())
# salt campaign bulk rate stop estimates, status
sums=[]
for _,r in sdf.iterrows():
 j=json.load(open(r.p));bulk=next((x for x in j['stop_events'] if x.get('phase')=='bulk'),None)
 if not bulk or not r.time or r.time<1:continue
 b=readtele(j);b=b[b.phase=='bulk'] if len(b) else b
 # endpoint bulk: stop m_g / t_bulk; note priming, afterflow, and carry tared offset
 m=bulk.get('m_stop_g');rate=m/r.time if m is not None else np.nan
 # slope limited by telemetry truncation; exclude priming first 2 sec, fit if 12+ data rows
 s=stats.linregress(b.t_s,b.m_g).slope if len(b)>=12 else np.nan
 sums.append(dict(idx=r.idx,tilt=r.tilt,rpm=r.rpm,tap=r.tap,stop_rate=rate,poll_rate=s,bulk_s=r.time,n=len(b)))
so=pd.DataFrame(sums);print('salt n',len(so));print(so.groupby(['tilt','rpm','tap']).stop_rate.agg(['size','mean','std']).round(4).to_string());print('same settings salt',so.query('tilt==40 and rpm==100 and tap==True')[['idx','stop_rate','poll_rate','bulk_s','n']].round(3).to_string(index=False))

# --- Executed notebook block 25 ---
a2=A[A.sigma_g.notna()]; active=a2.groupby('run').sigma_g.median();active=active[active>0].index; print('noise active',len(active),'A rows',len(A[A.run.isin(active)]),'sigma median',A[A.run.isin(active)].sigma_g.median(),'sd baseline per-run',A[A.run.isin(active)].groupby('run').delta_g.std().to_dict(),'absdrift median',A[A.run.isin(active)].drift_g.abs().median(),'shock count',int((A[A.run.isin(active)].shock_g.fillna(0)!=0).sum()))
print('C shocks among measured valid',len(C),sum(C.quality.eq('shock')),'C unsettled',sum(C.quality.eq('unsettled')))
for tilt in [0,45,90]:
 z=cs[(cs.powder=='salt')&(cs.tilt_deg==tilt)];print('3days',tilt,round(z['mean'].std()/z['mean'].mean()*100,1))
for name,cvs in [('salt',[.21093,.12656,.10184]),('AlSi10Mg',[.33866,.13458,.04455])]:
 print('\n',name)
 for tlt,c in zip([0,45,90],cvs):
  print(tlt,'MDD 6rev %',round(100*2.802*2**.5*c/np.sqrt(6),1),'revs', [int(np.ceil((2.802*2**.5*c/d)**2)) for d in [.03,.05,.10]])
print('between day floor 90',3.963*.09916)

# --- Executed notebook block 27 ---
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
# Curated E measurement: high-shock bench readouts unresolved (not negative physical tap quanta).
f.loc[['alsi10mg','silicon-110-200','sodium-sulfate'],'tap']=np.nan
f.to_csv(out/'feature_table.csv')
fig,ax=plt.subplots(1,2,figsize=(11.5,4.2),layout='constrained')
n=np.arange(3,201);k=(stats.norm.ppf(.975)+stats.norm.ppf(.8))*np.sqrt(2)
for lab,c,col in [('AlSi10Mg: 90°',.04455,'#0072B2'),('Salt: 90°',.10184,'#D55E00'),('AlSi10Mg: 45°',.13458,'#009E73'),('Salt: 45°',.12656,'#CC79A7')]:ax[0].plot(n,100*k*c/np.sqrt(n),label=lab,color=col,lw=2)
for lev in [3,5,10]:ax[0].axhline(lev,color='#999999',ls=':',lw=.8)
ax[0].set(xlabel='Single revolutions per batch and tilt',ylabel='Detectable feed-factor difference (%)',xlim=(3,200),ylim=(0,40));ax[0].legend(frameon=False,fontsize=8,loc='upper right')
for name,col in [('alsi10mg','#0072B2'),('salt','#D55E00'),('sodium-alginate','#CC79A7')]:
 z=f.loc[name];ax[1].plot([0,45,90],[z.ff0,z.ff45,z.ff90],marker='o',label=name,color=col,lw=2)
ax[1].set(xlabel='Downward tube tilt (degrees)',ylabel='Feed factor (mg/revolution)',xticks=[0,45,90]);ax[1].legend(frameon=False,fontsize=8)
fig.savefig(out/'resolution_and_tilt.png',dpi=250);fig.savefig(out/'resolution_and_tilt.pdf');plt.show()
fig,axes=plt.subplots(1,2,figsize=(11.5,4.1),layout='constrained')
for key,label,col in [('alsi','AlSi10Mg: fixed 100 rpm','#0072B2'),('de4dd913','Al 4047: fixed 100 rpm','#D55E00'),('56a01060','Al 4047: variable rpm','#CC79A7')]:
 a=files[key].query('phase=="bulk"');tm=a.t_s-a.t_s.min();axes[0].plot(tm,a.m_g,marker='.' if key!='alsi' else None,ms=2,lw=1.7,color=col,label=label)
axes[0].set(xlabel='Time since start of logged bulk phase (s)',ylabel='Accumulated bulk mass (g)',xlim=(0,58));axes[0].legend(frameon=False,fontsize=8,loc='upper left')
for key,label,col,lo,hi in [('alsi','AlSi10Mg (post-prime)','#0072B2',29,58),('de4dd913','Al 4047 (clogged)','#D55E00',8,35)]:
 z=files[key];b=z[z.phase=='bulk'];wr=win_rates(z,lo,hi);times=np.arange(lo,lo+2*len(wr),2)-b.t_s.min()+1
 axes[1].plot(times,wr*1000,'o-',lw=1.4,ms=3,color=col,label=label)
axes[1].set(xlabel='Time since start of logged bulk phase (s)',ylabel='Nonoverlapping 2-s rate (mg/s)',ylim=(-5,295));axes[1].legend(frameon=False,fontsize=8)
fig.savefig(out/'production_comparison.png',dpi=250);fig.savefig(out/'production_comparison.pdf');plt.show()
print('saved:',list(out.glob('*')))

# --- Executed notebook block 28 ---
z=files['de4dd913'];a=z[z.phase=='bulk'];wr=win_rates(z,8,35);mid=np.arange(8,8+2*len(wr),2)+1; rr=stats.linregress(mid[wr>0],np.log(wr[wr>0]));print('exploratory first 27s tau',-1/rr.slope,'r2',rr.rvalue**2,'p',rr.pvalue);print('de4 full total rate',4.17293/368.84,'end rate',json.load(open(glob.glob('/workspace/data/opt/production-al4047*/zero/trial_de4*')[0]))['stop_events'][0]['rate_slope_gps']);print('salt same 40 100 taps cv',so.query('tilt==40 and rpm==100 and tap==True').stop_rate.std()/so.query('tilt==40 and rpm==100 and tap==True').stop_rate.mean());
for key in ['alsi','de4dd913']:
 z=files[key];print('z steady',key,stats.linregress(z.query('phase=="bulk" and t_s>=30 and t_s<=58').t_s,z.query('phase=="bulk" and t_s>=30 and t_s<=58').m_g).slope if key=='alsi' else 'n/a')
print('resolution intermittent',2.802*np.sqrt(2*.13*.87/24),2.802*np.sqrt(2*.13*.87/48))