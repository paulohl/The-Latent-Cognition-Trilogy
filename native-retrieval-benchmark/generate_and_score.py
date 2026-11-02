#!/usr/bin/env python3
"""Synthetic DLI task diagnostic, v1. Python >=3.10; numpy, scikit-learn, matplotlib.
Run: python3 generate_and_score.py --out <directory> --seed 6821299
No network, pretrained model, or author implementation is used.
"""
import argparse, collections, csv, hashlib, json, math, random, re
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

SCENARIOS=['single_hop','paraphrase','two_hop','redundancy','poisoning','update','unanswerable','local_only','saturation','counterfactual']

def tokens(s): return re.findall(r'[a-z0-9]+',s.lower())
def dumpj(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def jsonl(p,rows): p.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))

def generate(seed):
    rng=random.Random(seed); rows=[]
    for split,n in [('train',60),('dev',20),('test',40)]:
        for g in range(n):
            pair_entity='Station-'+rng.randbytes(5).hex(); pair_site='Port-'+rng.randbytes(5).hex(); pair_alt='Port-'+rng.randbytes(5).hex()
            pair_id=f'{split}-pair-{g:03}'
            for scenario in SCENARIOS:
                eid=f'{split}-{g:03}-{scenario}'
                entity=pair_entity if scenario in ['single_hop','counterfactual'] else 'Station-'+rng.randbytes(5).hex()
                site=pair_site if scenario=='single_hop' else pair_alt if scenario=='counterfactual' else 'Port-'+rng.randbytes(5).hex()
                color=rng.choice(['amber','cobalt','ivory','teal','violet','silver'])
                mem=[]
                def doc(text,source='registry',date='2026-06-01'):
                    d={'id':rng.randbytes(8).hex(),'text':text,'source':source,'effective_date':date};mem.append(d);return d['id']
                query=f'Which port is the base of {entity}?'; local=''; ans=site; evidence=[]
                base=f'{entity} has base {site}.'
                if scenario=='paraphrase': query=f'At which harbor is {entity} stationed?'
                if scenario=='two_hop':
                    query=f'What is the beacon color at the base of {entity}?'
                    a=doc(base); b=doc(f'{site} has beacon color {color}.');ans=color;evidence=[[a,b]]
                elif scenario=='unanswerable':
                    ans='ABSTAIN'
                    doc(f'{entity} has supervisor Officer-{rng.randbytes(4).hex()}.')
                elif scenario=='local_only':
                    local=base+' Use the fact in this message; no memory lookup is needed.'
                else:
                    a=doc(base); evidence=[[a]]
                    if scenario=='redundancy':
                        for _ in range(7): evidence.append([doc(base)])
                    if scenario=='poisoning':
                        for _ in range(6): doc(f'{entity} has base Port-{rng.randbytes(5).hex()}. '+f'{entity} base port. '*4,source='untrusted')
                    if scenario=='update':
                        doc(f'{entity} has base Port-{rng.randbytes(5).hex()}.',date='2025-01-01')
                        doc(f'{entity} has base Port-{rng.randbytes(5).hex()}.',date='2027-01-01')
                target=128 if scenario=='saturation' else 32
                while len(mem)<target:
                    other='Station-'+rng.randbytes(5).hex(); port='Port-'+rng.randbytes(5).hex()
                    # Same-entity irrelevant relations and same-relation other entities.
                    text=(f'{other} has beacon color {rng.choice(["amber","cobalt","ivory","teal","violet","silver"])}.' if scenario=='two_hop' and len(mem)%3==0 else f'{entity} has supervisor Officer-{rng.randbytes(4).hex()}.' if len(mem)%4==0 else f'{other} has base {port}.')
                    doc(text)
                rng.shuffle(mem)
                if scenario=='local_only': evidence=[[]]
                rows.append({'id':eid,'split':split,'world_id':pair_id if scenario in ['single_hop','counterfactual'] else eid,
                    'pair_id':pair_id if scenario in ['single_hop','counterfactual'] else None,'scenario':scenario,
                    'query':query,'local_context':local,'as_of':'2026-06-30','memory':mem,
                    'labels':{'answer':ans,'answerable':ans!='ABSTAIN','retrieval_required':scenario!='local_only',
                        'hop_count':2 if scenario=='two_hop' else 0 if scenario in ['local_only','unanswerable'] else 1,
                        'acceptable_evidence_sets':evidence,'reason':'missing_evidence' if scenario=='unanswerable' else 'local_context' if scenario=='local_only' else 'memory_evidence'},
                    'provenance':{'kind':'synthetic','generator_version':'1.0','seed':seed}})
    # Controlled one-fact counterfactual: identical query, document IDs, order,
    # distractors and provenance. Only the correct base value is swapped.
    for r in rows:
        if r['scenario']=='counterfactual':
            original=next(x for x in rows if x['pair_id']==r['pair_id'] and x['scenario']=='single_hop')
            r['memory']=json.loads(json.dumps(original['memory']))
            r['labels']['acceptable_evidence_sets']=original['labels']['acceptable_evidence_sets']
            for d in r['memory']:
                d['text']=d['text'].replace(original['labels']['answer'],r['labels']['answer'])
    return rows

# Extractive decoder is deliberately shared: isolates retrieval/policy differences,
# not LLM fluency. It parses only supplied context, never labels or hidden world state.
def solve(row,docs,policy=True):
    entity=re.search(r'Station-[a-f0-9]+',row['query']).group()
    if row['local_context']:
        m=re.search(re.escape(entity)+r' has base (Port-[a-f0-9]+)',row['local_context'])
        if m:return m.group(1),[]
    candidates=[]
    for d in docs:
        if policy and (d['source']!='registry' or d['effective_date']>row['as_of']):continue
        m=re.search(re.escape(entity)+r' has base (Port-[a-f0-9]+)',d['text'])
        if m:candidates.append((d,m.group(1)))
    if policy:candidates.sort(key=lambda x:x[0]['effective_date'],reverse=True)
    if not candidates:return 'ABSTAIN',[]
    d,port=candidates[0]
    if 'beacon color' not in row['query']:return port,[d['id']]
    for e in docs:
        if policy and (e['source']!='registry' or e['effective_date']>row['as_of']):continue
        m=re.search(re.escape(port)+r' has beacon color ([a-z]+)',e['text'])
        if m:return m.group(1),[d['id'],e['id']]
    return 'ABSTAIN',[]

def bm25(query,docs):
    bags=[collections.Counter(tokens(d['text'])) for d in docs]; n=len(bags)
    df=collections.Counter(t for b in bags for t in b); avg=sum(map(lambda b:sum(b.values()),bags))/n
    score=[]
    for b in bags:
        dl=sum(b.values()); s=0
        for t in set(tokens(query)):
            f=b[t]; idf=math.log(1+(n-df[t]+.5)/(df[t]+.5))
            s+=idf*f*2.5/(f+1.5*(.25+.75*dl/avg))
        score.append(s)
    return sorted(range(n),key=lambda i:(-score[i],i))

def run(rows,out):
    methods=['no_memory','bm25_naive','bm25_policy','tfidf_policy','iterative_bm25_policy','full_memory_reference']
    predictions=[]
    for row in rows:
        if row['split']!='test':continue
        docs=row['memory']; b=bm25(row['query'],docs)
        vec=TfidfVectorizer(); mat=vec.fit_transform([d['text'] for d in docs]); sim=(mat@vec.transform([row['query']]).T).toarray().ravel(); tf=list(np.argsort(-sim,kind='stable'))
        for method in methods:
            gate=bool(not row['local_context']) and method!='no_memory'
            if not gate: selected=[]
            elif method=='full_memory_reference':selected=docs[:]
            elif method=='tfidf_policy':selected=[docs[i] for i in tf[:5]]
            elif method=='iterative_bm25_policy':
                first=[docs[i] for i in b[:3]]; selected=first[:]
                # Only a discovered first-hop value can drive the second query.
                found,_=solve({**row,'query':row['query'].replace('beacon color','port')},first)
                if found.startswith('Port-') and 'beacon color' in row['query']:
                    second=bm25(found+' beacon color',docs)
                    selected += [docs[i] for i in second if docs[i] not in first][:2]
                else:selected += [docs[i] for i in b[3:5]]
            else:selected=[docs[i] for i in b[:5]]
            answer,cited=solve(row,selected,policy=method!='bm25_naive')
            labels=row['labels']; gold=labels['acceptable_evidence_sets']; ids={d['id'] for d in selected}
            eligible=labels['answerable'] and labels['retrieval_required']
            recall=max((len(set(s)&ids)/len(s) for s in gold if s),default=0) if eligible else None
            complete=any(set(s)<=ids for s in gold) if eligible else None
            grounded=(answer==labels['answer'] and (answer=='ABSTAIN' or any(set(s)<=set(cited) for s in gold)))
            poisoned=any(d['source']=='untrusted' and d['id'] in cited for d in docs)
            predictions.append({'id':row['id'],'scenario':row['scenario'],'method':method,'prediction':answer,'cited_ids':cited,'retrieved_ids':sorted(ids),
                'exact_match':int(answer==labels['answer']),'grounded_exact_match':int(grounded),'gate_correct':int(gate==labels['retrieval_required']),
                'evidence_recall':recall,'complete_evidence':None if complete is None else int(complete),'retrieved_count':len(selected),
                'poison_citation':int(poisoned)})
    scores=[]
    for method in methods:
        for scenario in ['ALL']+SCENARIOS:
            p=[p for p in predictions if p['method']==method and (scenario=='ALL' or p['scenario']==scenario)]
            rec=[p for p in p if p['evidence_recall'] is not None]
            def avg(key,arr=p):return sum(x[key] for x in arr)/len(arr) if arr else None
            scores.append({'method':method,'scenario':scenario,'n':len(p),'answer_em':avg('exact_match'),'grounded_em':avg('grounded_exact_match'),
                'gate_accuracy':avg('gate_correct'),'evidence_n':len(rec),'evidence_recall_at_budget':avg('evidence_recall',rec),
                'complete_evidence_at_budget':avg('complete_evidence',rec),'mean_retrieved':avg('retrieved_count'),'poison_citation_rate':avg('poison_citation')})
    jsonl(out/'predictions.jsonl',predictions)
    with (out/'baseline_scores.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    return scores

def validate(rows):
    assert len(rows)==1200 and len({r['id'] for r in rows})==1200
    worlds=collections.defaultdict(set); entity_splits=collections.defaultdict(set)
    for r in rows:
        worlds[r['world_id']].add(r['split'])
        for entity in re.findall(r'(?:Station|Port)-[a-f0-9]+',r['query']+' '+r['local_context']+' '+' '.join(d['text'] for d in r['memory'])):entity_splits[entity].add(r['split'])
        ids={d['id'] for d in r['memory']}
        assert len(ids)==len(r['memory'])
        assert all(set(s)<=ids for s in r['labels']['acceptable_evidence_sets'])
        answer,cites=solve(r,r['memory'])
        assert answer==r['labels']['answer'],(r['id'],answer)
        assert answer=='ABSTAIN' or any(set(s)<=set(cites) for s in r['labels']['acceptable_evidence_sets'])
    assert all(len(s)==1 for s in worlds.values())
    assert all(len(s)==1 for s in entity_splits.values())
    pairs=collections.defaultdict(list)
    for r in rows:
        if r['pair_id']:pairs[r['pair_id']].append(r)
    assert all(len(p)==2 and p[0]['query']==p[1]['query'] and p[0]['labels']['answer']!=p[1]['labels']['answer'] for p in pairs.values())
    for a,b in pairs.values():
        assert len(a['memory'])==len(b['memory'])
        assert sum(x!=y for x,y in zip(a['memory'],b['memory']))==1
        assert all({k:v for k,v in x.items() if k!='text'}=={k:v for k,v in y.items() if k!='text'} for x,y in zip(a['memory'],b['memory']))
    return {'status':'passed','examples':len(rows),'split_counts':dict(collections.Counter(r['split'] for r in rows)),
            'scenario_counts':dict(collections.Counter(r['scenario'] for r in rows)),'counterfactual_pairs':len(pairs),
            'checks':['unique example and per-memory IDs','evidence IDs resolve','reference solver recovers every gold answer',
                      'reference citations satisfy minimal evidence sets','world and entity-disjoint splits','paired query equality, changed answer, and exactly one changed memory text'],
            'note':'Schema and rule validation, not independent human annotation or evidence of language-model performance.'}

def schema():
    st={'type':'string'}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:dli-native-retrieval:v1','title':'DLI Native Retrieval Diagnostic v1','type':'object','additionalProperties':False,
      'required':['id','split','world_id','pair_id','scenario','query','local_context','as_of','memory','labels','provenance'],
      'properties':{'id':st,'split':{'enum':['train','dev','test']},'world_id':st,'pair_id':{'type':['string','null']},'scenario':{'enum':SCENARIOS},'query':st,'local_context':st,'as_of':{'type':'string','format':'date'},
      'memory':{'type':'array','minItems':32,'items':{'type':'object','additionalProperties':False,'required':['id','text','source','effective_date'],'properties':{'id':st,'text':st,'source':{'enum':['registry','untrusted']},'effective_date':{'type':'string','format':'date'}}}},
      'labels':{'type':'object','additionalProperties':False,'required':['answer','answerable','retrieval_required','hop_count','acceptable_evidence_sets','reason'],'properties':{'answer':st,'answerable':{'type':'boolean'},'retrieval_required':{'type':'boolean'},'hop_count':{'enum':[0,1,2]},'acceptable_evidence_sets':{'type':'array','items':{'type':'array','items':st,'uniqueItems':True}},'reason':{'enum':['missing_evidence','local_context','memory_evidence']}}},
      'provenance':{'type':'object','additionalProperties':False,'required':['kind','generator_version','seed'],'properties':{'kind':{'const':'synthetic'},'generator_version':{'const':'1.0'},'seed':{'type':'integer'}}}}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path('native-retrieval-output'));ap.add_argument('--seed',type=int,default=6821299);args=ap.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    rows=generate(args.seed);audit=validate(rows);jsonl(out/'benchmark.jsonl',rows);dumpj(out/'schema.json',schema());dumpj(out/'validation.json',audit)
    scores=run(rows,out)
    # No timing comparisons: index construction and retrieval are not timed consistently.
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods=[s['method'] for s in scores if s['scenario']=='ALL'];fig,ax=plt.subplots(figsize=(11,5))
    a=np.array([[next(s['answer_em'] for s in scores if s['method']==m and s['scenario']==c) for c in SCENARIOS] for m in methods])
    im=ax.imshow(a,vmin=0,vmax=1,cmap='Blues');ax.set_xticks(range(10),[s.replace('_','\n') for s in SCENARIOS],fontsize=8);ax.set_yticks(range(len(methods)),methods,fontsize=9)
    for i in range(len(methods)):
        for j in range(10):ax.text(j,i,f'{a[i,j]:.0%}',ha='center',va='center',color='white' if a[i,j]>.65 else 'black',fontsize=9)
    ax.set_title('Synthetic native-retrieval diagnostic | test n=400 | answer exact match');fig.colorbar(im,ax=ax,label='Exact match');fig.tight_layout();fig.savefig(out/'baseline_heatmap.png',dpi=170);plt.close(fig)
    dumpj(out/'manifest.json',{'version':'1.0','seed':args.seed,'paper_doi':'10.2139/ssrn.6821299','examples':len(rows),'memory_records':sum(len(r['memory']) for r in rows),'test_examples':400,
       'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.name in ['benchmark.jsonl','schema.json','baseline_scores.csv','validation.json']}})
    print(json.dumps({'audit':audit,'overall':[s for s in scores if s['scenario']=='ALL']},indent=2))
if __name__=='__main__':main()
