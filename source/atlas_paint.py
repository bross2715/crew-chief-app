"""Vectorize the paint classes of the COTA Corner Atlas map (page 1 image) into our meter frame and store them in
data.json COTA corners.paint = {red,blue,green,gold: 'M x y L ... Z'} (x east, y north, meters). Also stores per-turn names and track feature text.
The image was registered to corners.fl.F by fitting the asphalt skeleton (mean error under 1 px).
Usage: python3 -I source/atlas_paint.py <p1.png> <xf.npy> <atlas_features.json>"""
import sys,json,cv2,numpy as np
im=cv2.imread(sys.argv[1]); xf=np.load(sys.argv[2]); feat=json.load(open(sys.argv[3]))
s,th,tx,ty=xf; c,sn=np.cos(th),np.sin(th)
rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB).astype(int); R,G,B=rgb[...,0],rgb[...,1],rgb[...,2]
M={'red':(R>150)&(G<95)&(B<125)&(R-B>50),'blue':(B>95)&(B-R>45)&(R<95)&(G>55)&(G<115),'green':(G>85)&(G-R>35)&(R<85)&(B<135)&(G>B-10),'gold':(R>170)&(G>120)&(B<110)&(R-B>80)}
def tom(px,py):
    X=px-tx; Y=py-ty; xr=X*c+Y*sn; yr=-X*sn+Y*c   # inverse rotation
    return xr/s, -yr/s
out={}
for k,m in M.items():
    m=cv2.morphologyEx(m.astype(np.uint8)*255,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    m=cv2.resize(m,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC); m=cv2.GaussianBlur(m,(0,0),2.2); m=(m>127).astype(np.uint8)
    cs,_=cv2.findContours(m,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE); d=[]; n=0
    for ct in cs:
        if cv2.contourArea(ct)<14*9: continue
        ct=cv2.approxPolyDP(ct,2.2,True)[:,0,:]/3.0
        if len(ct)<3: continue
        xs,ys=tom(ct[:,0],ct[:,1]); d.append('M'+'L'.join('%.1f %.1f'%(a,b) for a,b in zip(xs,ys))+'Z'); n+=len(ct)
    out[k]=''.join(d); print(k,len(cs),'pieces kept',len(d),'pts',n,'chars',len(out[k]))
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; C=t['corners']
C['paint']=out; C['atlas']={k:{'name':v['name'],'features':v['features']} for k,v in feat.items()}
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
