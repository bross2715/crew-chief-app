"""Apply Grokbot's DE-28 target vs average numbers (cota-target-vs-average-line JSON) to COTA corner rows.
sc = his median turn time minus the mean of his best 3 (turn windows only); you[0] = median slowest point of 10 laps;
pro[0] = Pro Line slowest; geo tgmph = target slowest (his own best clean lap). Then rerun combo.py.
Usage: python3 -I source/ingest_de28.py <json>"""
import json,sys
src=json.load(open(sys.argv[1])); D=json.load(open('data.json'))
t=[x for x in D['tracks'] if x['track']=='COTA'][0]; C=t['corners']; R={r['t']:r for r in C['rows']}; G=C['geo']
def tier(g): return 'locked in' if g<=0.2 else 'small gain' if g<=0.5 else 'getting there' if g<=1.0 else 'needs work'
for tr in src['turns']:
    k=tr['turn']; r=R.get(k); g=G.get(k)
    if not r or not g: continue
    gap=tr['gap_target_vs_average']['turn_time_s']; av=(tr['average'].get('slowest') or {}).get('mph'); tg=(tr['target'].get('his_highest_slowest_mph') or tr['target'].get('slowest') or {}).get('mph'); pro=tr['target'].get('proline_slowest_mph')
    r['sc']=round(float(gap),2); r['st']=tier(r['sc']); g['st']=r['st']
    if av: r['you']=[av,None]
    if pro: r['pro']=[pro,(r.get('pro') or [None,None])[1]]
    if tg: g['tgmph']=tg
    print(k,r['sc'],r['st'],r['you'],r['pro'],g.get('tgmph'))
R['T14']['tip']=g14=("T14 has no brake or lift on any lap. The slowest point is the T14 entry (about 58 mph for you, 62 target). The old 75 vs 93 were exit speeds. The loss is a slower drive off T13: you exit T13 and T14 10 to 14 mph down on the Pro Line, so fix T13 first.")
G['T14']['fix']=g14
json.dump(D,open('data.json','w'),separators=(',',':'),ensure_ascii=False)
