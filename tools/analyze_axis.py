"""Analyze an LX-01 serial record; acceptance is diagnostic, not electrical qualification."""
import argparse
import json
from pathlib import Path
import statistics

def analyze(text, phase='observe'):
    rows=[]
    for line in text.splitlines():
        if not line.startswith('AXIS available='):continue
        fields={k:int(v) for item in line.split()[1:] if '=' in item for k,v in [item.split('=',1)]}
        if fields.get('active')==1 and fields.get('valid')==1:rows.append(fields)
    if not rows:return {'passed':False,'checks':{'active_samples_present':False},'scope':'diagnostic record only'}
    required={'pin','samples','raw','filtered','mv_est','age_ms','elapsed_ms','errors'}
    complete=all(required<=r.keys() for r in rows)
    if not complete:return {'passed':False,'checks':{'complete_fields':False},'scope':'diagnostic record only'}
    intervals=[b['elapsed_ms']-a['elapsed_ms'] for a,b in zip(rows,rows[1:])]
    counts=[b['samples']-a['samples'] for a,b in zip(rows,rows[1:])]
    duration=(rows[-1]['elapsed_ms']-rows[0]['elapsed_ms'])/1000
    checks={'record_at_least_4_seconds':duration>=4,
            'gpio5_only':all(r['pin']==5 for r in rows),
            'raw_and_filter_in_range':all(0<=r['raw']<=4095 and 0<=r['filtered']<=4095 for r in rows),
            'no_driver_errors':all(r['errors']==0 for r in rows),
            'fresh_samples':all(0<=r['age_ms']<=100 for r in rows),
            'monotonic_session':bool(intervals) and all(0<t<=300 for t in intervals),
            'acquisition_advances':bool(counts) and all(c>0 for c in counts)}
    if phase=='ground':checks['ground_estimate_within_100mv']=all(0<=r['mv_est']<=100 for r in rows)
    raw=[r['raw'] for r in rows];filtered=sorted(r['filtered'] for r in rows)
    report={'passed':all(checks.values()),'phase':phase,'checks':checks,'reports':len(rows),'duration_s':duration,
            'raw_min':min(raw),'raw_median':statistics.median(raw),'raw_max':max(raw),
            'filtered_p95_minus_p5':filtered[int((len(filtered)-1)*.95)]-filtered[int((len(filtered)-1)*.05)],
            'mv_est_median':statistics.median(r['mv_est'] for r in rows),
            'scope':'Diagnostic record only; circuit identity, DMM agreement, input loading and safe power states need separate evidence'}
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('--phase',choices=['observe','ground'],default='observe')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=analyze(args.log.read_text(),args.phase)
    rendered=json.dumps(report,indent=2)+'\n'
    if args.output:args.output.write_text(rendered)
    print(rendered,end='');raise SystemExit(0 if report['passed'] else 1)
