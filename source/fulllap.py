"""Stitch every corner piece into one closed lap line for You and Target (data.json COTA corners.fl).
Pieces are projected onto a smoothed full-lap centerline; overlaps are tapered together, gaps are eased across.
Run after smooth_lines.py.  Usage: python3 -I source/fulllap.py"""
import json,math
ST=2.0; CLAMP=9.0
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; C=t['corners']; G=C['geo']
order=['T1','T2','T3','T4','T5','T6','6A','6B','T12','T13','T14','T15','T16-T18','T19','T20']
F=[list(map(float,p)) for p in C['full']]
if math.hypot(F[0][0]-F[-1][0],F[0][1]-F[-1][1])>1: F.append(F[0][:])
def resample(P,step):
    cum=[0.0]
    for i in range(1,len(P)): cum.append(cum[-1]+math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]))
    L=cum[-1];n=int(round(L/step));out=[];j=0
    for k in range(n):
        a=k*L/n
        while j<len(cum)-2 and cum[j+1]<a:j+=1
        u=max(0,min(1,(a-cum[j])/((cum[j+1]-cum[j]) or 1)));out.append([P[j][0]+u*(P[j+1][0]-P[j][0]),P[j][1]+u*(P[j+1][1]-P[j][1])])
    return out,L
def psm(P,sig,step):
    n=len(P);K=int(sig*2.5/step);ker=[math.exp(-.5*((i*step)/sig)**2) for i in range(-K,K+1)];out=[]
    for k in range(n):
        sx=sy=w=0
        for i,kv in enumerate(ker):
            q=(k+i-K)%n;sx+=kv*P[q][0];sy+=kv*P[q][1];w+=kv
        out.append([sx/w,sy/w])
    return out
def psm1(v,sig,step):
    n=len(v);K=int(sig*2.5/step);ker=[math.exp(-.5*((i*step)/sig)**2) for i in range(-K,K+1)];out=[]
    for k in range(n):
        s=w=0
        for i,kv in enumerate(ker):
            q=(k+i-K)%n;s+=kv*v[q];w+=kv
        out.append(s/w)
    return out
Fr,L0=resample(F,ST);n=len(Fr);Fs=psm(Fr,10.0,L0/n);step=L0/n
def norm(i):
    a=Fs[(i-1)%n];b=Fs[(i+1)%n];dx,dy=b[0]-a[0],b[1]-a[1];m=math.hypot(dx,dy) or 1;return -dy/m,dx/m
NRM=[norm(i) for i in range(n)]
def proj(P):
    best=None
    for i in range(n):
        a=Fs[i];b=Fs[(i+1)%n];dx,dy=b[0]-a[0],b[1]-a[1];L2=dx*dx+dy*dy or 1e-9
        u=max(0,min(1,((P[0]-a[0])*dx+(P[1]-a[1])*dy)/L2));qx,qy=a[0]+u*dx,a[1]+u*dy;d=math.hypot(P[0]-qx,P[1]-qy)
        if best is None or d<best[0]:best=(d,(i+u)*step,((dx*(P[1]-a[1])-dy*(P[0]-a[0]))/math.sqrt(L2)))
    return best[1],best[2]
# direction check with T1 cl
c1=G['T1']['cl'];s0,_=proj(c1[0]);s1,_=proj(c1[len(c1)//2]);d=(s1-s0)%L0
if d>L0/2:
    Fs=Fs[::-1];NRM=[norm(i) for i in range(n)]
    print('reversed full loop to match driving direction')
sf=C['sf'];ssf,_=proj(sf[:2])
def piece(g,nm):
    sgs=g[nm]['s'];pts=[];fl=[]
    for st,P in sgs:
        for q in P:
            if pts and math.hypot(q[0]-pts[-1][0],q[1]-pts[-1][1])<.01: continue
            pts.append(q);fl.append(1 if st=='grey_dotted' else 0)
    pr=[proj(q) for q in pts];S=[];m=None
    for s,o in pr:
        if m is None:u=s
        else:
            u=s
            while u-m>L0/2:u-=L0
            while m-u>L0/2:u+=L0
        S.append(u);m=u
    return S,[o for s,o in pr],fl
def build(nm):
    acc=[[] for _ in range(n)]
    for k in order:
        g=G[k]
        if nm not in g:continue
        S,O,fl=piece(g,nm)
        if S[-1]<S[0]:S,O,fl=S[::-1],O[::-1],fl[::-1]
        mm=-1e9;A=[];B=[];Fq=[]
        for s,o,f in zip(S,O,fl):
            mm=max(mm,s)
            if A and abs(mm-A[-1])<.5:B[-1]=(B[-1]+o)/2;continue
            A.append(mm);B.append(o);Fq.append(f)
        i0=int(math.ceil(A[0]/step));i1=int(math.floor(A[-1]/step));j=0
        for q in range(i0,i1+1):
            s=q*step
            while j<len(A)-2 and A[j+1]<s:j+=1
            w=max(0,min(1,(s-A[j])/((A[j+1]-A[j]) or 1)));o=B[j]+(B[j+1]-B[j])*w;f=Fq[j] if w<.5 else Fq[j+1]
            e=min(s-A[0],A[-1]-s);wt=min(e,60.0)+3.0
            acc[q%n].append((o,f,wt))
    off=[None]*n;flag=[1]*n
    for i in range(n):
        if acc[i]:
            sw=sum(a[2] for a in acc[i]);off[i]=sum(a[0]*a[2] for a in acc[i])/sw;flag[i]=0 if sum(a[2] for a in acc[i] if a[1]==0)>=sw/2 else 1
    cov=[i for i in range(n) if off[i] is not None]
    for a,b in zip(cov,cov[1:]+[cov[0]+n]):
        gap=b-a-1
        if gap<=0:continue
        oa=off[a%n];ob=off[b%n]
        for q in range(1,gap+1):
            w=q/(gap+1);e=.5-.5*math.cos(math.pi*w);off[(a+q)%n]=oa+(ob-oa)*e;flag[(a+q)%n]=1
    off=[max(-CLAMP,min(CLAMP,v)) for v in psm1(off,4.0,step)]
    xy=[[round(Fs[i][0]+off[i]*NRM[i][0],1),round(Fs[i][1]+off[i]*NRM[i][1],1)] for i in range(n)]
    return xy,flag
tg,ftg=build('tg');yo,fyo=build('you')
k0=int(round(ssf/step))%n
rot=lambda v:v[k0:]+v[:k0]
C['fl']={'st':round(step,3),'L':round(L0,1),'n':n,'F':[[round(p[0],1),round(p[1],1)] for p in rot(Fs)],'tg':rot(tg),'you':rot(yo),'ftg':''.join(map(str,rot(ftg))),'fyou':''.join(map(str,rot(fyo)))}
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print('full lap',round(L0),'m',n,'pts; read share tg',round(1-sum(ftg)/n,2),'you',round(1-sum(fyo)/n,2))
