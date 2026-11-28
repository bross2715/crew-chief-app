"""Register each Corner Atlas page image to the app's meter frame.
Page 1 (whole map) is already registered (xf.npy). Each per-turn page is matched to page 1's asphalt mask by
normalized cross-correlation over rotation and scale, then polished. Output: source/atlas_pages.json
{page:{img,turn,M:[a,b,c,d,e,f]}} where meters x = a*px+b*py+c, y = d*px+e*py+f."""
import cv2,numpy as np,json,glob,sys
from scipy.optimize import minimize
b=cv2.imread('/tmp/atlas/p1-000.png'); xf=np.load('/tmp/atlas/xf.npy')
def asph(im):
    rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB).astype(int); R,G,B=rgb[...,0],rgb[...,1],rgb[...,2]
    m=(R<90)&(G<90)&(B<100)&(abs(R-G)<25); return cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
mb=cv2.GaussianBlur(asph(b).astype(np.float32),(0,0),1.5)
files=sorted(glob.glob('/tmp/atlas/pp-*.png'))[1:]
turns=['T1','T2','T3','T4','T5','T6','6A','6B','T12','T13','T14','T15','T16','T17','T18','T16-T18','T19','T20']
out={}
for f,tn in zip(files,turns):
    im=cv2.imread(f); m=asph(im).astype(np.float32); H,W=m.shape
    best=(-1,)
    for sc in np.arange(0.12,0.26,0.01):
        small=cv2.resize(m,None,fx=sc,fy=sc,interpolation=cv2.INTER_AREA)
        for rot in range(0,360,4):
            ctr=(small.shape[1]/2,small.shape[0]/2); R=cv2.getRotationMatrix2D(ctr,rot,1.0)
            cs,sn=abs(R[0,0]),abs(R[0,1]); nw=int(small.shape[0]*sn+small.shape[1]*cs); nh=int(small.shape[0]*cs+small.shape[1]*sn)
            R[0,2]+=nw/2-ctr[0]; R[1,2]+=nh/2-ctr[1]
            t=cv2.warpAffine(small,R,(nw,nh),flags=cv2.INTER_LINEAR); t=cv2.GaussianBlur(t,(0,0),1.5)
            if nw>=mb.shape[1] or nh>=mb.shape[0]: continue
            r=cv2.matchTemplate(mb,t,cv2.TM_CCOEFF_NORMED); _,mx,_,loc=cv2.minMaxLoc(r)
            if mx>best[0]: best=(mx,sc,rot,loc,R.copy(),nw,nh)
    mx,sc,rot,loc,R,nw,nh=best
    # transform page px -> page1 px:  p1 = loc + R @ (sc*px)  (R is 2x3 acting on scaled coords)
    A=np.vstack([R,[0,0,1]])@np.diag([sc,sc,1.0]); A[0,2]+=loc[0]; A[1,2]+=loc[1]
    # polish by maximizing correlation with small param perturbations
    def warp(p):
        a=np.array([[p[0],p[1],p[4]],[p[2],p[3],p[5]]],np.float32); return a
    p0=[A[0,0],A[0,1],A[1,0],A[1,1],A[0,2],A[1,2]]
    mask_page=cv2.GaussianBlur(m,(0,0),1.5)
    def cost(p):
        w=cv2.warpAffine(mask_page,warp(p),(mb.shape[1],mb.shape[0]),flags=cv2.INTER_LINEAR)
        v=cv2.warpAffine(np.ones_like(mask_page),warp(p),(mb.shape[1],mb.shape[0]))>0.5
        if v.sum()<100: return 1
        a=w[v]; c=mb[v]; return -float(np.corrcoef(a,c)[0,1])
    # similarity-constrained polish: params (s,th,tx,ty)
    s0=np.hypot(A[0,0],A[1,0]); th0=np.arctan2(A[1,0],A[0,0])
    def sim(q):
        s,th,tx,ty=q; return [s*np.cos(th),-s*np.sin(th),s*np.sin(th),s*np.cos(th),tx,ty]
    r=minimize(lambda q:cost(sim(q)),[s0,th0,A[0,2],A[1,2]],method='Nelder-Mead',options={'xatol':1e-4,'fatol':1e-5,'maxiter':600})
    q=r.x; P=sim(q); ncc=-r.fun
    # compose with page1 px -> meters: px1 = s1*R(th1)*[x,-y]+t  =>  [x,-y] = R^-1 (px1-t)/s1
    s1,th1,tx1,ty1=xf; c1,sn1=np.cos(th1),np.sin(th1)
    # px1 = P[:2] ; build page px -> px1 affine
    Aff=np.array([[P[0],P[1],P[4]],[P[2],P[3],P[5]]])
    # px1 -> meters: X=(px1x-tx1), Y=(px1y-ty1); xr=(X*c1+Y*sn1)/s1 ; yr=(-X*sn1+Y*c1)/s1 ; x=xr ; y=-yr
    Mm=np.array([[c1/s1,sn1/s1,0],[sn1/s1,-c1/s1,0]])  # y=-yr = (X*sn1 - Y*c1)/s1
    T1=np.array([[1,0,-tx1],[0,1,-ty1],[0,0,1]]); full=Mm@T1@np.vstack([Aff,[0,0,1]])
    out[tn]={'img':f.split('/')[-1],'M':[round(float(v),6) for v in full.ravel()[:6]],'ncc':round(ncc,3),'w':W,'h':H,'pxm':round(float(np.hypot(full[0,0],full[1,0])),4)}
    print(tn,f.split('/')[-1],'ncc0',round(mx,3),'ncc',round(ncc,3),'m per px',out[tn]['pxm'],'(px/m %.2f)'%(1/out[tn]['pxm']),'rot0',rot)
json.dump(out,open('source/atlas_pages.json','w'),indent=1)
