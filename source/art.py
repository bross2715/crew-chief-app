"""Embed the COTA overlay pack's full-circuit vector art (ChatGPT/Claude track design) into data.json COTA corners.art.
The art lives in the same frame as our lines: svg x = x east, svg y = -y north (meters). Decimals trimmed to 0.1 m.
Replaces the traced paint. Usage: python3 -I source/art.py /path/to/COTA_full.svg"""
import re,sys,json
s=open(sys.argv[1]).read()
i=s.index('<g transform="matrix('); j=s.index('>',i)+1; inner=s[j:s.rindex('</g></svg>')]
pal={'#dce1d5':'ground'}
def r1(m): return ('%.1f'%float(m.group(0))).rstrip('0').rstrip('.') if '.' in m.group(0) else m.group(0)
inner=re.sub(r'-?\d+\.\d{2,}',r1,inner).replace('-0 ','0 ').replace(' -0,',' 0,')
inner=re.sub(r'\s+id="[^"]*"','',inner) if False else inner
D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; C=t['corners']
C['art']=inner; C.pop('paint',None)
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print('art chars',len(inner),'paths',inner.count('<path'),'groups',re.findall(r'<g id="([^"]+)"',inner))
