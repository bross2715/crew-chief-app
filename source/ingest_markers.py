"""Coach markers on the target line (BRAKE, TURN IN, APEX, EXIT) from Grokbot's DE-28 JSON -> data.json COTA corners.geo[*].mk = [[label,x,y]].
BRAKE carries the target speed at the brake point, APEX the target slowest point. Usage: python3 -I source/ingest_markers.py <json>"""
import json,sys
src=json.load(open(sys.argv[1])); D=json.load(open('data.json')); t=[x for x in D['tracks'] if x['track']=='COTA'][0]; G=t['corners']['geo']
KIND={'brake':'BRAKE','turn_in':'TURN IN','apex':'APEX','apex_min_speed':'APEX','track_out':'EXIT'}
for tr in src['turns']:
    g=G.get(tr['turn'])
    if not g: continue
    tgt=tr['target']; bm=(tgt.get('brake_or_lift') or {}).get('mph'); mk=[]; seen=set()
    for p in tgt['line_points']:
        lab=KIND.get(p['kind'])
        if not lab or 'x' not in p: continue
        if lab in seen and lab!='EXIT': continue
        seen.add(lab)
        txt=lab+(' %d'%bm if lab=='BRAKE' and bm else ' %d'%g['tgmph'] if lab=='APEX' and g.get('tgmph') else '')
        mk.append([txt,round(p['x'],1),round(p['y'],1)])
    g['mk']=mk; print(tr['turn'],[m[0] for m in mk])
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
