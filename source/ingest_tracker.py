"""Embed Grokbot's COTA sector tracker into data.json as crew.trk.

Usage: python3 -I source/ingest_tracker.py /path/to/cota-sector-tracker.json
Then: python3 -I source/build.py
Add new sessions to META below (id -> tag, kind, rebased) when Grokbot appends one.
"""
import json, sys
META = {
    'N24': ('Nov 24', 'practice', False),
    'B': ('Run 2', 'practice', False),
    'D': ('Run 4', 'race', True),
    'R27': ('Run 5', 'race', True),
    'R7P': ('Run 7', 'practice', True),
    'R7R': ('Run 7', 'race', True),
}
K = {'S1': 'S1', 'S2': 'S2', 'S3-4': 'S3+S4', 'S5': 'S5', 'S6-7': 'S6+S7'}
LEAGUE_SCALE = 1.03919  # Pro Line sector x this = the league target

def main(path):
    tk = json.load(open(path))
    pro = tk['pro_line']['groups']
    tg = {k: round(pro[v] * LEAGUE_SCALE, 2) for k, v in K.items()}
    out = []
    for s in tk['sessions']:
        if s['id'] not in META:
            raise SystemExit('Add %s to META first' % s['id'])
        tag, kind, rb = META[s['id']]
        g = s['summary']['groups']
        gap, iq, nv = {}, {}, {}
        for k, v in K.items():
            m = g[v]['median_valid']
            # old-clock sessions: S1 and S6+S7 are not trusted
            gap[k] = None if (not rb and k in ('S1', 'S6-7')) else round(m - tg[k], 2)
            iq[k] = g[v]['iqr']
            nv[k] = g[v]['n_valid']
        out.append({'id': s['id'], 'tag': tag + ' · ' + kind.capitalize(), 'kind': kind,
                    'laps': s['summary']['laps_recorded'], 'gap': gap, 'tg': tg, 'iqr': iq, 'n': nv, 'rebased': rb})
    d = json.load(open('data.json'))
    for t in d['tracks']:
        if t['track'] == 'COTA':
            t['crew']['trk'] = out
    json.dump(d, open('data.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    print('embedded', len(out), 'sessions')

if __name__ == '__main__':
    main(sys.argv[1])
