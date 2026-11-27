#!/usr/bin/env python3
"""Reproduce the numerical audit from the supplied SI extraction.
Run: python reproduce_audit.py
Requires Python 3, numpy, pandas, scipy. No network or e14c required.
Tables contain rounded SI values; no unavailable raw telemetry is imputed.
"""
from pathlib import Path
from collections import defaultdict
import re, json, math, itertools, sys
import numpy as np
import pandas as pd
from scipy import stats
import scipy
HERE=Path(__file__).resolve().parent
OUT=HERE/'reproduced'; OUT.mkdir(exist_ok=True)
text=(HERE/'si_extracted.txt').read_text()
pattern=r'^\s*(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(ok|overshoot|cycle-budget|stalled|fw-error|not-tared)\s+([\d.−-]+|–)\s+([\d.−-]+|–)\s*$'
rows=[]
for line in text.splitlines():
    m=re.match(pattern,line)
    if not m: continue
    idx,label,taps,settings,outcome,t,e=m.groups()
    conv=lambda s: float(s.replace('−','-')) if s!='–' else np.nan
    rows.append(dict(idx=int(idx),label=label,taps=taps,settings=settings,
                     outcome=outcome,t=conv(t),e=conv(e)))
assert len(rows)==103
c1=pd.DataFrame(rows[:60]); c2=pd.DataFrame(rows[60:])
assert c1.idx.tolist()==list(range(60))
assert c2.idx.tolist()==list(range(43))
c1.to_csv(OUT/'campaign1_tableS2.csv',index=False)
c2.to_csv(OUT/'campaign2_tableS4.csv',index=False)
groups={'hand-tuned':c1[c1.label.str.contains('baseline')],
        'bo-005':c1.query('44<=idx<=51'),
        'corner-09':c1.query('52<=idx<=59')}
summary=[]
for name,d in groups.items():
    for col in ['t','e']:
        a=d[col].to_numpy(); a=abs(a) if col=='e' else a
        summary.append(dict(group=name,metric=col,n=len(a),median=np.median(a),
                            mean=np.mean(a),min=min(a),max=max(a),sd=np.std(a,ddof=1)))
summary=pd.DataFrame(summary); summary.to_csv(OUT/'validation_summary.csv',index=False)

def exact_tied_rank_p(x,y):
    # Two-sided exact randomization: twice the smaller inclusive rank-sum tail.
    n=len(x); ranks=stats.rankdata(np.r_[x,y]); center=n*ranks.mean()
    observed=sum(ranks[:n]); threshold=abs(observed-center)
    sums=np.array([sum(ranks[list(ix)]) for ix in itertools.combinations(range(len(ranks)),n)])
    return float(min(1.0, 2*min(np.mean(sums<=observed+1e-10), np.mean(sums>=observed-1e-10))))

comparisons=[]
for a,b in [('bo-005','hand-tuned'),('bo-005','corner-09'),('corner-09','hand-tuned')]:
    for col in ['t','e']:
        x=groups[a][col].to_numpy();y=groups[b][col].to_numpy()
        if col=='e': x=abs(x);y=abs(y)
        mw=stats.mannwhitneyu(x,y,method='exact',alternative='two-sided')
        comparisons.append(dict(a=a,b=b,metric=col,U=mw.statistic,
             p_exact_untied=mw.pvalue,p_label_permutation=exact_tied_rank_p(x,y),
             HL_shift=np.median((x[:,None]-y).ravel())))
comparisons=pd.DataFrame(comparisons)
comparisons.to_csv(OUT/'mann_whitney_comparisons.csv',index=False)

def bootstrap_dist(x):
    # Enumerate n resampled observations via multinomial occupancy counts.
    x=np.asarray(x);n=len(x);dist=defaultdict(float)
    def compositions(left,k,prefix=()):
        if k==1:
            yield prefix+(left,);return
        for i in range(left+1):yield from compositions(left-i,k-1,prefix+(i,))
    for counts in compositions(n,n):
        p=math.factorial(n)/math.prod(math.factorial(c) for c in counts)/n**n
        dist[float(np.median(np.repeat(x,counts)))]+=p
    return dict(sorted(dist.items()))
def distq(dist,qs=(.025,.975)):
    return np.array(list(dist))[np.searchsorted(np.cumsum(list(dist.values())),qs)].tolist()
intervals={}
for name,d in groups.items():
    for col in ['t','e']:
        vals=d[col].to_numpy(); vals=abs(vals) if col=='e' else vals
        intervals[name+'_'+col]=distq(bootstrap_dist(vals))
bd=bootstrap_dist(groups['hand-tuned'].t);od=bootstrap_dist(groups['bo-005'].t)
rd=defaultdict(float)
for a,pa in bd.items():
    for b,pb in od.items():rd[a/b]+=pa*pb
intervals['ratio_time_medians']=distq(dict(sorted(rd.items())))

def hl_exact_time_ci(x,y):
    n=len(x);m=len(y)
    unull=np.array([sum(i+1 for i in ix)-n*(n+1)/2
                   for ix in itertools.combinations(range(n+m),n)])
    q=max(k for k in range(n*m+1) if np.mean(unull<=k)<=.025)
    diffs=np.sort((np.asarray(x)[:,None]-np.asarray(y)).ravel())
    return dict(interval=[diffs[q],diffs[-q-1]],confidence=1-2*np.mean(unull<=q))
intervals['HL_bo_minus_baseline_time']=hl_exact_time_ci(groups['bo-005'].t,groups['hand-tuned'].t)
intervals['HL_bo_minus_corner_time']=hl_exact_time_ci(groups['bo-005'].t,groups['corner-09'].t)

p1=c1[c1.label.str.match('corner-')]
p2=c2[c2.label.str.match('corner-') & ~c2.outcome.isin(['not-tared','fw-error'])]
paired=p1.merge(p2,on='label',suffixes=('_1','_2'))
assert len(paired)==16
paired.to_csv(OUT/'paired_corners.csv',index=False)
ok=paired.query('outcome_1=="ok" and outcome_2=="ok"')
dt=ok.t_2-ok.t_1
overshoot_lost=sum((paired.outcome_1=='overshoot')&(paired.outcome_2!='overshoot'))
overshoot_gained=sum((paired.outcome_1!='overshoot')&(paired.outcome_2=='overshoot'))
paired_stats=dict(n_both_ok=len(ok),median_dt=float(np.median(dt)),mean_dt=float(np.mean(dt)),
    wilcoxon_p=float(stats.wilcoxon(dt,method='exact').pvalue),
    mean_absolute_error_change=float(np.mean(abs(ok.e_2)-abs(ok.e_1))),
    overshoot_lost=int(overshoot_lost),overshoot_gained=int(overshoot_gained),
    mcnemar_p=float(stats.binomtest(min(overshoot_lost,overshoot_gained),overshoot_lost+overshoot_gained,.5).pvalue))
for key,x,y in [('time',paired.t_1,paired.t_2),('abs_error',abs(paired.e_1),abs(paired.e_2)),('signed_error',paired.e_1,paired.e_2)]:
    sr=stats.spearmanr(x,y);paired_stats[key+'_rho']=float(sr.statistic);paired_stats[key+'_p']=float(sr.pvalue)
z=(paired.t_2-paired.t_1).to_numpy();rr=stats.rankdata(abs(z));obs=sum(rr[z>0]);tot=sum(rr)
sums=np.array([np.dot(sign,rr) for sign in itertools.product([0,1],repeat=len(z))])
paired_stats['all16_exact_signed_rank_signflip_p']=float(np.mean(abs(sums-tot/2)>=abs(obs-tot/2)-1e-10))

# Screening effects and actual factorial resolution.
settings=['bulk_tilt','trickle_tilt','tap_tilt','rpm','switch','delta']
screen=p1.copy()
for col,vals in zip(settings,np.array([list(map(float,s.split())) for s in screen.settings]).T):screen[col]=vals
screen['bulk_taps']=screen.taps.str.split('/').str[0].map({'off':0,'2hz':2})
screen['trickle_taps']=screen.taps.str.split('/').str[1].map({'off':0,'2hz':2})
factors=['bulk_taps','trickle_taps']+settings
screen_rows=[]
for col in factors:
    for level,d in screen.groupby(col):
        screen_rows.append(dict(setting=col,level=level,n=len(d),n_ok=int(sum(d.outcome=='ok')),
             time_ok=d.loc[d.outcome=='ok','t'].mean(),mean_abs_error=abs(d.e).mean(),fails=int(sum(d.outcome!='ok'))))
pd.DataFrame(screen_rows).to_csv(OUT/'screening_effects.csv',index=False)
X=screen[factors].to_numpy();X=np.where(X==X.min(axis=0),-1,1)
assert np.array_equal(X.T@X,16*np.eye(8))
defining={k:[','.join(np.array(factors)[list(ix)]) for ix in itertools.combinations(range(8),k)
             if abs(np.prod(X[:,ix],axis=1).sum())==16] for k in [3,4]}
assert not defining[3] and defining[4]

# Verify constant LOO baseline with historic failure encoding.
train=c1.iloc[:42].copy();encoded_error=abs(train.e.to_numpy())
jams=train.outcome.isin(['cycle-budget','stalled']).to_numpy()
encoded_error[jams]=np.maximum(encoded_error[jams],20)
constant_rmse={}
for col,vals in [('time',train.t.to_numpy()),('abs_error',encoded_error)]:
    pred=(vals.sum()-vals)/(len(vals)-1)
    constant_rmse[col]=float(np.sqrt(np.mean((pred-vals)**2)))

# Exact count/run arithmetic and final-score flag checks.
band_flags=[]
for campaign,df,offset in [(1,c1,-1),(2,c2,-2)]:
    for row in df.itertuples():
        band=float(row.settings.split()[offset])
        if row.outcome=='ok' and abs(row.e)>band:
            band_flags.append(dict(campaign=campaign,index=row.idx,label=row.label,error=row.e,delta=band))
# Outline power: IID equal-dispersion log-normal trials and exact MW critical region.
rng=np.random.default_rng(20261127);power=[]
for n,m,ratio in [(8,8,2),(8,8,1.5),(4,8,2)]:
    null=np.array([sum(i+1 for i in ix)-n*(n+1)/2 for ix in itertools.combinations(range(n+m),n)])
    crit=max(k for k in range(n*m//2+1) if 2*np.mean(null<=k)<=.05)
    a=rng.normal(0,.26,(200000,n));b=rng.normal(np.log(ratio),.26,(200000,m))
    u=(a[:,:,None]>b[:,None,:]).sum(axis=(1,2))
    power.append(dict(n=n,m=m,ratio=ratio,critical_U=crit,power=float(np.mean((u<=crit)|(u>=n*m-crit)))))
results=dict(versions=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),
    bootstrap_intervals=intervals,paired=paired_stats,constant_LOO_RMSE=constant_rmse,
    factorial_defining_words=defining,recorded_ok_outside_displayed_band=band_flags,
    campaign1_counts=train.outcome.value_counts().to_dict(),campaign2_counts=c2.outcome.value_counts().to_dict(),
    time_median_ratio=float(groups['hand-tuned'].t.median()/groups['bo-005'].t.median()),
    execution_sum_seconds=float(train.t.sum()),success_lower_8of8=float(stats.beta.ppf(.05,8,1)),
    overshoot_upper_0of8=float(stats.beta.ppf(.95,1,8)),outline_power_simulations=power)
(OUT/'audit_results.json').write_text(json.dumps(results,indent=2))
assert np.isclose(groups['bo-005'].t.median(),78.4)
assert np.isclose(paired_stats['wilcoxon_p'],.578125)
assert np.isclose(comparisons.iloc[0].p_exact_untied,.00404040404040404)

s3block=text[text.index('Table S3:'):text.index('Table S4:')]
range_rows=[]
for line in s3block.splitlines():
    m=re.match(r'^\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+([\d.]+)\s+(ok|fw-error)\s+([\d.]+)\s+(-?[\d.]+)\s+(\d+)\s*$',line)
    if not m:continue
    date,time,target,outcome,t,e,taps=m.groups()
    range_rows.append(dict(date=date,time=time,target_g=float(target),outcome=outcome,t_s=float(t),error_mg=float(e),taps=int(taps)))
range_df=pd.DataFrame(range_rows)
assert len(range_df)==6
range_df['abs_relative_error_percent']=abs(range_df.error_mg)/(range_df.target_g*1000)*100
range_df.to_csv(OUT/'dose_range_tableS3.csv',index=False)

print(summary.to_string(index=False))
print(comparisons.to_string(index=False))
print(json.dumps(results,indent=2))
print('All audit assertions passed. Results:',OUT)
