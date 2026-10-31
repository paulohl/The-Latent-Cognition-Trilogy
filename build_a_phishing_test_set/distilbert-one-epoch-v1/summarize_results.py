#!/usr/bin/env python3
"""Audit completed predictions against source labels and summarize the fixed run."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def writecsv(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 results=ROOT/'results'
 provenance=json.loads((results/'provenance.json').read_text());assert provenance['status']=='completed'
 rows=[json.loads(l) for l in (ROOT/'dataset.jsonl').read_text().splitlines()]
 byid={r['id']:r for r in rows};assert len(byid)==1180
 predictions=list(csv.DictReader((results/'predictions.csv').open()))
 assert len(predictions)==380 and len({r['id'] for r in predictions})==380
 assert not ({r['id'] for r in predictions}&{r['id'] for r in rows if r['split']=='train'})
 for r in predictions:assert int(r['gold'])==byid[r['id']]['phishing_label'] and r['split']==byid[r['id']]['split']
 scores=list(csv.DictReader((results/'distilbert_scores.csv').open()))
 for s in scores:
  rr=[r for r in predictions if r['split']==s['split']]
  for name,y,p in [('tn',0,0),('fp',0,1),('fn',1,0),('tp',1,1)]:assert int(s[name])==sum(int(r['gold'])==y and int(r['prediction'])==p for r in rr)
 lookup={r['id']:int(r['prediction']) for r in predictions}
 pairs={}
 for r in rows:
  if r['split']=='hard_negative_challenge':pairs.setdefault(r['pair_id'],[]).append(r)
 pair_rate=sum(all(lookup[r['id']]==r['phishing_label'] for r in pair) for pair in pairs.values())/len(pairs)
 families=[]
 for fam in sorted({r['family_id'] for r in rows if r['split']=='hard_negative_challenge'}):
  rr=[r for r in rows if r['split']=='hard_negative_challenge' and r['family_id']==fam]
  families.append(dict(family_id=fam,n=4,false_positives=sum(r['phishing_label']==0 and lookup[r['id']]==1 for r in rr),false_negatives=sum(r['phishing_label']==1 and lookup[r['id']]==0 for r in rr),both_members_correct_rate=sum(all(lookup[r['id']]==r['phishing_label'] for r in pair) for pair in pairs.values() if pair[0]['family_id']==fam)/2))
 writecsv(ROOT/'hard_negative_family_scores.csv',families)
 old=list(csv.DictReader((ROOT/'baseline_scores_input.csv').open()))
 comparison=[{k:s.get(k,'') for k in ['split','baseline','n','accuracy','precision','recall','f1','false_positive_rate','tn','fp','fn','tp','both_members_correct_rate']} for s in old]
 for s in scores:
  if s['split']=='validation':continue
  comparison.append({**s,'split':'synthetic_test' if s['split']=='test' else s['split'],'both_members_correct_rate':pair_rate if s['split']=='hard_negative_challenge' else ''})
 writecsv(ROOT/'comparison.csv',comparison)
 audit=dict(status='passed',prediction_rows=380,train_overlap=0,input_sha256=hashlib.sha256((ROOT/'dataset.jsonl').read_bytes()).hexdigest(),label_and_split_match=True,all_confusion_counts_recomputed=True,hard_negative_pair_success=pair_rate,full_training_completed=True,epochs=provenance['epochs'],trainable_parameters=provenance['trainable_parameters'])
 (ROOT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps({'scores':scores,'hard_negative_pair_success':pair_rate,'audit':audit,'provenance':provenance},indent=2))

if __name__=='__main__':main()
