"""Embed Grokbot's fitted target line (cota-peak-line-fitted JSON) into data.json COTA corners.geo[*].tg.
Usage: python3 -I source/ingest_peakline.py <peak-line.json>"""
import json,sys
src=json.load(open(sys.argv[1])); D=json.load(open('data.json'))
t=[x for x in D['tracks'] if x['track']=='COTA'][0]; G=t['corners']['geo']; n=0
for tr in src['turns']:
    g=G.get(tr['turn'])
    if not g: continue
    segs=[['green_solid' if s['style']=='peak_solid' else 'grey_dotted',s['pts']] for s in tr['line']['segments']]
    g['tg']={'s':segs}
    m=tr.get('target_slowest_mph')
    g['tgmph']=m if isinstance(m,(int,float)) else None
    n+=1
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
print('turns with target line:',n)
