#!/usr/bin/env python3
"""Paired provenance-filter ablation, using the existing synthetic benchmark.
python3 run_provenance_test.py --benchmark-dir ../native-retrieval-benchmark --out .
The ZIP includes benchmark.jsonl and generate_and_score.py beside this script,
so its default --benchmark-dir works after unpacking there.
"""
import argparse,copy,csv,hashlib,importlib.util,json
from pathlib import Path

METHODS=['bm25_naive','bm25_postfilter','bm25_prefilter_trust','bm25_prefilter_trust_time','iterative_bm25_prefilter_trust_time']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--benchmark-dir',type=Path,default=Path(__file__).parent);ap.add_argument('--out',type=Path,default=Path(__file__).parent);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('base',a.benchmark_dir/'generate_and_score.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    data_path=a.benchmark_dir/'benchmark.jsonl';test=[json.loads(s) for s in data_path.open() if s.strip()];test=[r for r in test if r['split']=='test'];assert len(test)==400
    forged=[]
    for original in test:
        if original['scenario']!='poisoning':continue
        r=copy.deepcopy(original)
        attack_ids=[d['id'] for d in r['memory'] if d['source']=='untrusted']
        for d in r['memory']:
            if d['id'] in attack_ids:d.update(source='registry',effective_date='2026-06-15')
        r['attack_annotation']={'condition':'forged_trust_metadata','attacker_document_ids':attack_ids,'truth_policy':'Preserve original authenticated-world gold; forged metadata is an attack, not new truth.'}
        forged.append(r)
    base.jsonl(a.out/'forged_metadata_cases.jsonl',forged)
    results=[]
    for condition,rows in [('original',test),('forged_trust_metadata',forged)]:
        for row in rows:
            attack_ids=set(row.get('attack_annotation',{}).get('attacker_document_ids',[d['id'] for d in row['memory'] if d['source']=='untrusted']))
            # Evaluation-only fields never reach retrieval or the answer decoder.
            view={k:row[k] for k in ['query','local_context','as_of','memory']}
            docs=view['memory'];ranks=base.bm25(view['query'],docs)
            for method in METHODS:
                def allowed(d):
                    if 'prefilter' not in method:return True
                    return d['source']=='registry' and ('trust_time' not in method or d['effective_date']<=view['as_of'])
                # Hold full-corpus BM25 scores and IDF fixed; mask before top-k.
                ranking=[i for i in ranks if allowed(docs[i])]
                if view['local_context']:selected=[]
                elif method.startswith('iterative'):
                    first=[docs[i] for i in ranking[:3]];selected=first[:]
                    found,_=base.solve({**view,'query':view['query'].replace('beacon color','port')},first)
                    if found.startswith('Port-') and 'beacon color' in view['query']:
                        second=base.bm25(found+' beacon color',docs)
                        selected += [docs[i] for i in second if allowed(docs[i]) and docs[i] not in first][:2]
                    else:selected += [docs[i] for i in ranking[3:5]]
                else:selected=[docs[i] for i in ranking[:5]]
                answer,cites=base.solve(view,selected,policy=method!='bm25_naive')
                labels=row['labels'];gold=labels['acceptable_evidence_sets'];eligible=labels['answerable'] and labels['retrieval_required'];ids={d['id'] for d in selected}
                results.append({'condition':condition,'id':row['id'],'scenario':row['scenario'],'method':method,'answer':answer,'evidence_ids':cites,'retrieved_ids':sorted(ids),
                    'answer_em':int(answer==labels['answer']),'grounded_em':int(answer==labels['answer'] and (answer=='ABSTAIN' or any(set(g)<=set(cites) for g in gold))),
                    'complete_evidence':int(any(set(g)<=ids for g in gold)) if eligible else None,
                    'abstain':int(answer=='ABSTAIN'),'attack_citation':int(bool(set(cites)&attack_ids)),
                    'attack_retrieved':int(bool(ids&attack_ids)),'retrieved_count':len(selected)})
    base.jsonl(a.out/'predictions.jsonl',results)
    scores=[]
    for condition,scenarios in [('original',['ALL']+base.SCENARIOS),('forged_trust_metadata',['poisoning'])]:
        for scenario in scenarios:
            for method in METHODS:
                p=[x for x in results if x['condition']==condition and x['method']==method and (scenario=='ALL' or x['scenario']==scenario)]
                def avg(k):
                    vals=[x[k] for x in p if x[k] is not None];return sum(vals)/len(vals) if vals else None
                scores.append({'condition':condition,'scenario':scenario,'method':method,'n':len(p),**{k:avg(k) for k in ['answer_em','grounded_em','complete_evidence','abstain','attack_citation','attack_retrieved','retrieved_count']}})
    with (a.out/'scores.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    # Confirm matched original baselines exactly reproduce the saved experiment.
    prior=list(csv.DictReader((a.benchmark_dir/'baseline_scores.csv').open()))
    for new,old in [('bm25_naive','bm25_naive'),('bm25_postfilter','bm25_policy')]:
        for scenario in ['ALL']+base.SCENARIOS:
            observed=next(s for s in scores if s['condition']=='original' and s['scenario']==scenario and s['method']==new)
            oldrow=next(s for s in prior if s['scenario']==scenario and s['method']==old)
            assert observed['answer_em']==float(oldrow['answer_em'])
    assert len(results)==2200 and len(forged)==40 and len(scores)==60
    assert all(r['retrieved_count']<=5 for r in results)
    base.dumpj(a.out/'audit.json',{'status':'passed','original_test_episodes':400,'forged_metadata_episodes':40,'methods':5,'prediction_records':len(results),'score_rows':len(scores),
        'input_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),
        'checks':['all original naive and postfilter per-scenario answer scores match prior experiment','all runs respect total five-passage budget','only query, local_context, as_of and memory passed to decoder','full-corpus BM25 IDF and scores held fixed across single-pass filtering conditions'],
        'forged_metadata_note':'Gold truth is retained from the original authenticated world; metadata tags are deliberately compromised. This is not an ordinary valid-source update.'})
    print(json.dumps([s for s in scores if s['scenario'] in ['ALL','poisoning']],indent=2))
if __name__=='__main__':main()
