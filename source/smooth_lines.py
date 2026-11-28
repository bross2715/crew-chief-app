"""Snap every corner line onto the drawn track ribbon and smooth it in (distance, lateral) space.
Reads raw lines from source/raw_lines.json (created on first run from data.json), writes tg/you/pro back to data.json.
Each output line: s=[[style,[[x,y]...]]...] at 2 m spacing, a0=start distance along the ribbon, st=2.
Usage: python3 -I source/smooth_lines.py"""
import json,math,os
ST=2.0; CLAMP=9.0; SIG=6.0
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; G=t['corners']['geo']
RAW='source/raw_lines.json'
if not os.path.exists(RAW):
    json.dump({k:dict({n:G[k][n] for n in('tg','you','pro') if n in G[k]},cl=G[k]['cl']) for k in G},open(RAW,'w'),separators=(',',':'))
R=json.load(open(RAW))
def smooth_cl(cl,step=2.0,sig=10.0):
    cum=[0.0]
    for i in range(1,len(cl)): cum.append(cum[-1]+math.hypot(cl[i][0]-cl[i-1][0],cl[i][1]-cl[i-1][1]))
    n=int(cum[-1]/step)+1;pts=[];j=0
    for k in range(n):
        a=k*step
        while j<len(cum)-2 and cum[j+1]<a:j+=1
        u=(a-cum[j])/((cum[j+1]-cum[j]) or 1);u=max(0,min(1,u));pts.append([cl[j][0]+u*(cl[j+1][0]-cl[j][0]),cl[j][1]+u*(cl[j+1][1]-cl[j][1])])
    pts.append(list(cl[-1]))
    K=int(sig*2.5/step);ker=[math.exp(-.5*((i*step)/sig)**2) for i in range(-K,K+1)];out=[]
    m=len(pts)
    for k in range(m):
        sx=sy=w=0
        for i,kv in enumerate(ker):
            q=k+i-K
            if 0<=q<m:sx+=kv*pts[q][0];sy+=kv*pts[q][1];w+=kv
        out.append([round(sx/w,1),round(sy/w,1)])
    out[0]=[float(cl[0][0]),float(cl[0][1])];out[-1]=[float(cl[-1][0]),float(cl[-1][1])]
    return out
def prep(cl):
    cum=[0.0]
    for i in range(1,len(cl)): cum.append(cum[-1]+math.hypot(cl[i][0]-cl[i-1][0],cl[i][1]-cl[i-1][1]))
    return cum
def project(P,cl,cum):
    best=None
    for i in range(len(cl)-1):
        ax,ay=cl[i];bx,by=cl[i+1];dx,dy=bx-ax,by-ay;L2=dx*dx+dy*dy or 1e-9
        u=max(0,min(1,((P[0]-ax)*dx+(P[1]-ay)*dy)/L2));qx,qy=ax+u*dx,ay+u*dy
        d=math.hypot(P[0]-qx,P[1]-qy)
        if best is None or d<best[0]:
            L=math.sqrt(L2);best=(d,cum[i]+u*L,((dx*(P[1]-ay)-dy*(P[0]-ax))/L))
    return best[1],best[2]
def at(a,cl,cum):
    a=max(0,min(cum[-1],a));i=0
    while i<len(cum)-2 and cum[i+1]<a:i+=1
    L=cum[i+1]-cum[i] or 1e-9;u=(a-cum[i])/L;dx,dy=cl[i+1][0]-cl[i][0],cl[i+1][1]-cl[i][1];n=math.hypot(dx,dy) or 1
    return cl[i][0]+u*dx,cl[i][1]+u*dy,-dy/n,dx/n
def lane(sgs,cl,cum):
    pts=[];sty=[]
    for st,P in sgs:
        for q in P: pts.append(q);sty.append(st=='grey_dotted')
    pr=[project(q,cl,cum) for q in pts]
    fwd=pr[-1][0]-pr[0][0]
    if fwd<0: pr=pr[::-1];sty=sty[::-1]
    A=[];O=[];S=[];m=-1e9
    for (a,o),d in zip(pr,sty):
        m=max(m,a);A.append(m);O.append(o);S.append(d)
    # collapse equal a
    ua=[];uo=[];us=[]
    for a,o,d in zip(A,O,S):
        if ua and abs(a-ua[-1])<.5: uo[-1]=(uo[-1]+o)/2;us[-1]=us[-1] and d;continue
        ua.append(a);uo.append(o);us.append(d)
    if len(ua)<2: return None
    a0=math.ceil(ua[0]/ST)*ST;a1=math.floor(ua[-1]/ST)*ST;n=int((a1-a0)/ST)+1
    if n<3: return None
    G2=[];D2=[];j=0
    for k in range(n):
        a=a0+k*ST
        while j<len(ua)-2 and ua[j+1]<a:j+=1
        w=(a-ua[j])/((ua[j+1]-ua[j]) or 1);o=uo[j]+(uo[j+1]-uo[j])*max(0,min(1,w));G2.append(max(-CLAMP,min(CLAMP,o)));D2.append(us[j] and us[j+1])
    K=int(SIG*2.5/ST);ker=[math.exp(-.5*((i*ST)/SIG)**2) for i in range(-K,K+1)];sm=[]
    for k in range(n):
        s=w=0
        for i,kv in enumerate(ker):
            q=k+i-K
            if 0<=q<n:s+=kv*G2[q];w+=kv
        sm.append(s/w)
    sm[0]=G2[0]*.5+sm[0]*.5;sm[-1]=G2[-1]*.5+sm[-1]*.5
    xy=[]
    for k in range(n):
        x,y,nx,ny=at(a0+k*ST,cl,cum);xy.append([round(x+sm[k]*nx,2),round(y+sm[k]*ny,2)])
    segs=[];cur=[xy[0]];cd=D2[0]
    for k in range(1,n):
        if D2[k]==cd:cur.append(xy[k])
        else:
            cur.append(xy[k]);segs.append([('grey_dotted' if cd else 'X'),cur]);cur=[xy[k]];cd=D2[k]
    segs.append([('grey_dotted' if cd else 'X'),cur])
    return a0,segs,max(abs(v) for v in sm)
rep={}
for k,g in G.items():
    cl=smooth_cl(R[k]['cl']);cum=prep(cl);g['cl']=cl
    for name,sty in(('tg','green_solid'),('you','orange_dashed'),('pro','white_solid')):
        raw=R.get(k,{}).get(name)
        if not raw: continue
        out=lane(raw['s'],cl,cum)
        if not out: continue
        a0,segs,mo=out
        for s in segs:
            if s[0]=='X': s[0]=sty
        g[name]={'s':segs,'a0':a0,'st':ST}
        rep[(k,name)]=(len(segs),round(mo,1))
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print(len(rep),'lines smoothed; max |offset| m:',max(v[1] for v in rep.values()))
