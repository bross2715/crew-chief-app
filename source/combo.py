"""Add whole-section views (Esses, 6A to T12, T13 to T15, T16 to T20) cut from the stitched lap.
Times are the sector tracker's measured group times (target and your last race median), not the per-turn model.
Run after fulllap.py.  Usage: python3 -I source/combo.py"""
import json,math
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; C=t['corners']; fl=C['fl']; n=fl['n']; st=fl['st']
last=[s for s in t['crew']['trk'] if s.get('rebased')][-1]
SEC={s['id']:s for s in t['report']['sectors']}
GROUPS=[('T2-T6','S2',['T2','T3','T4','T5','T6'],'Esses T2 to T6'),('6A-T12','S3-4',['6A','6B','T12'],'6A to T12'),('T13-T15','S5',['T13','T14','T15'],'T13 to T15'),('T16-T20','S6-7',['T16-T18','T19','T20'],'T16 to T20')]
F0={'S2':('S2','S2'),'S3-4':('S3','S4'),'S5':('S5','S5'),'S6-7':('S6','S7')}
R={r['t']:r for r in C['rows']}
def tier(pct): return 'locked in' if pct<=1.5 else 'small gain' if pct<=3 else 'getting there' if pct<=5 else 'needs work'
def segs(P,flags,sty):
    out=[];cur=[P[0]];cd=flags[0]=='1'
    for k in range(1,len(P)):
        d=flags[k]=='1'
        if d==cd:cur.append(P[k])
        else:cur.append(P[k]);out.append(['grey_dotted' if cd else sty,cur]);cur=[P[k]];cd=d
    out.append(['grey_dotted' if cd else sty,cur]);return out
cg={};cr=[]
for name,gk,members,label in GROUPS:
    a,b=F0[gk];f0=SEC[a]['f0'];f1=SEC[b]['f1'];i0=int(round(f0*n));i1=min(n,int(round(f1*n)))
    sl=lambda v:v[i0:i1+1]
    cl=sl(fl['F']);ftg=sl(list(fl['ftg']));fyo=sl(list(fl['fyou']))
    xs=[p[0] for p in cl];ys=[p[1] for p in cl];mx=sum(xs)/len(xs);my=sum(ys)/len(ys)
    sxx=sum((x-mx)**2 for x in xs);syy=sum((y-my)**2 for y in ys);sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    th=0.5*math.atan2(2*sxy,sxx-syy)
    if (cl[-1][0]-cl[0][0])*math.cos(th)+(cl[-1][1]-cl[0][1])*math.sin(th)<0: th+=math.pi
    eh=round((90-math.degrees(th))%360)
    tw=last['tg'][gk];gap=last['gap'][gk];yw=round(tw+gap,2);pct=gap/tw*100;stt=tier(pct)
    mem=[R[m] for m in members if m in R]
    ymin=min((r['you'] for r in mem if r.get('you') and r['you'][0]),key=lambda q:q[0]);pmin=min((r['pro'] for r in mem if r.get('pro') and r['pro'][0]),key=lambda q:q[0])
    per='; '.join('%s %s vs %s mph'%(r['t'],r['you'][0] if r.get('you') else '?',r['pro'][0] if r.get('pro') else '?') for r in mem)
    ssum=sum(r['sc'] for r in mem if r.get('sc') is not None)
    tip=("You lose %.2f s a lap in this whole section (%.1f%% over the target, median of every lap in your last race, +-0.5 s). Slowest points, you against the Pro Line: %s. "
         "The single turn gaps add to only %.2f s, so they read low: they come from one lap each. Trust this section number."%(gap,pct,per,ssum))
    cg[name]={'combo':True,'label':label,'dir':'','st':stt,'cl':cl,'eh':eh,'tgmph':None,'tw':tw,'yw':yw,'fix':tip,
        'tg':{'s':segs(sl(fl['tg']),ftg,'green_solid'),'a0':0.0,'st':st},'you':{'s':segs(sl(fl['you']),fyo,'orange_dashed'),'a0':0.0,'st':st}}
    cr.append({'t':name,'dir':'','raw':None,'sc':round(gap,2),'st':stt,'you':ymin,'pro':pmin,'tip':tip,'combo':True,'label':label})
C['cg']=cg;C['cr']=cr
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print({k:(v['tw'],v['yw'],v['st'],v['eh'],len(v['cl'])) for k,v in cg.items()})
