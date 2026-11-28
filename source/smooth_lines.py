"""Snap every corner line onto the drawn track ribbon, smooth it in (distance, lateral) space, and extend it
over the whole ribbon piece (borrowing the other line where it has no read, else holding its last side).
Reads raw lines from source/raw_lines.json; writes tg/you/pro + smoothed cl back to data.json.
Each output line: s=[[style,[[x,y]...]]...] at 2 m spacing, a0=0, st=2, covered parts solid, extended parts grey_dotted.
Usage: python3 -I source/smooth_lines.py"""
import json,math
ST=2.0; CLAMP=9.0; SIG=6.0
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; G=t['corners']['geo']
R=json.load(open('source/raw_lines.json'))
STY={'tg':'green_solid','you':'orange_dashed','pro':'white_solid'}
def smooth_cl(cl,step=2.0,sig=10.0):
    cum=[0.0]
    for i in range(1,len(cl)): cum.append(cum[-1]+math.hypot(cl[i][0]-cl[i-1][0],cl[i][1]-cl[i-1][1]))
    n=int(cum[-1]/step)+1;pts=[];j=0
    for k in range(n):
        a=k*step
        while j<len(cum)-2 and cum[j+1]<a:j+=1
        u=max(0,min(1,(a-cum[j])/((cum[j+1]-cum[j]) or 1)));pts.append([cl[j][0]+u*(cl[j+1][0]-cl[j][0]),cl[j][1]+u*(cl[j+1][1]-cl[j][1])])
    pts.append(list(cl[-1]))
    K=int(sig*2.5/step);ker=[math.exp(-.5*((i*step)/sig)**2) for i in range(-K,K+1)];out=[];m=len(pts)
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
def gsm(v,sig):
    n=len(v);K=int(sig*2.5/ST);ker=[math.exp(-.5*((i*ST)/sig)**2) for i in range(-K,K+1)];out=[]
    for k in range(n):
        s=w=0
        for i,kv in enumerate(ker):
            q=k+i-K
            if 0<=q<n:s+=kv*v[q];w+=kv
        out.append(s/w)
    return out
def read(sgs,cl,cum,n):
    """own offsets on the full 2 m grid (None where no read)"""
    pts=[q for st,P in sgs for q in P]
    pr=[project(q,cl,cum) for q in pts]
    if pr[-1][0]-pr[0][0]<0: pr=pr[::-1]
    A=[];O=[];m=-1e9
    for a,o in pr:
        m=max(m,a)
        if A and abs(m-A[-1])<.5: O[-1]=(O[-1]+o)/2;continue
        A.append(m);O.append(o)
    if len(A)<2: return None
    i0=int(math.ceil(A[0]/ST));i1=int(math.floor(A[-1]/ST))
    if i1-i0<2: return None
    off=[None]*n;j=0
    for k in range(max(0,i0),min(n-1,i1)+1):
        a=k*ST
        while j<len(A)-2 and A[j+1]<a:j+=1
        w=max(0,min(1,(a-A[j])/((A[j+1]-A[j]) or 1)));off[k]=max(-CLAMP,min(CLAMP,O[j]+(O[j+1]-O[j])*w))
    cov=[k for k in range(n) if off[k] is not None]
    sm=gsm([off[k] for k in cov],SIG)
    for idx,k in enumerate(cov):off[k]=sm[idx]
    return off
def extend(off,other,n):
    """fill None: borrow other's offsets (continuity-corrected), else hold-and-ease; returns offsets, dotted flags"""
    cov=[o is not None for o in off];out=list(off);dot=[not c for c in cov]
    first=cov.index(True);last=n-1-cov[::-1].index(True)
    for side,rng in((-1,range(first-1,-1,-1)),(1,range(last+1,n))):
        edge=first if side<0 else last
        eo=off[edge];oo=other[edge] if other and other[edge] is not None else None
        for k in rng:
            d=abs(k-edge)*ST
            if other and other[k] is not None:
                base=other[k]+((eo-oo) if oo is not None else 0)*math.exp(-d/20.0)
            else:
                base=eo*(0.6+0.4*math.exp(-d/40.0))
            out[k]=base
    # smooth extended zones lightly so joins are clean
    sm=gsm(out,3.0)
    return [max(-CLAMP,min(CLAMP,v)) for v in sm],dot
rep=0;mo=0
for k,g in G.items():
    cl=smooth_cl(R[k]['cl']);cum=prep(cl);g['cl']=cl;n=int(cum[-1]/ST)+1
    own={nm:(read(R[k][nm]['s'],cl,cum,n) if nm in R[k] else None) for nm in STY}
    for nm in STY:
        off=own[nm]
        if off is None: continue
        other=own['tg'] if nm!='tg' else own['you']
        if nm=='pro': other=own['tg']
        oo,dot=extend(off,other,n)
        xy=[]
        for kk in range(n):
            x,y,nx,ny=at(kk*ST,cl,cum);xy.append([round(x+oo[kk]*nx,2),round(y+oo[kk]*ny,2)])
        segs=[];cur=[xy[0]];cd=dot[0]
        for kk in range(1,n):
            if dot[kk]==cd:cur.append(xy[kk])
            else:
                cur.append(xy[kk]);segs.append(['grey_dotted' if cd else STY[nm],cur]);cur=[xy[kk]];cd=dot[kk]
        segs.append(['grey_dotted' if cd else STY[nm],cur])
        g[nm]={'s':segs,'a0':0.0,'st':ST};rep+=1;mo=max(mo,max(abs(v) for v in oo))
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print(rep,'lines, max |offset| m',round(mo,1))
