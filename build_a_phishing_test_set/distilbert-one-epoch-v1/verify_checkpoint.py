#!/usr/bin/env python3
"""Reload final fitted weights and independently reproduce all held-out decisions."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
from pathlib import Path
import csv,json,time
import torch
from transformers import AutoTokenizer,AutoModelForSequenceClassification
ROOT=Path(__file__).resolve().parent

def main():
 torch.set_num_threads(4)
 path=ROOT/'results/final_model'
 tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
 model=AutoModelForSequenceClassification.from_pretrained(path,local_files_only=True,attn_implementation='sdpa').eval()
 rows=[json.loads(l) for l in (ROOT/'dataset.jsonl').read_text().splitlines()]
 rows=[r for r in rows if r['split']!='train']
 predictions={r['id']:int(r['prediction']) for r in csv.DictReader((ROOT/'results/predictions.csv').open())}
 assert len(rows)==len(predictions)==380
 start=time.time();checked=0
 with torch.inference_mode():
  for start_index in range(0,len(rows),4):
   batch=rows[start_index:start_index+4]
   encoded=tokenizer([r['email_text'] for r in batch],padding=True,truncation=True,max_length=512,return_tensors='pt')
   pred=model(**encoded).logits.argmax(-1).tolist()
   for r,p in zip(batch,pred):assert p==predictions[r['id']],r['id']
   checked+=len(batch)
 report=dict(status='passed',reloaded_final_checkpoint=True,matched_predictions=checked,total_predictions=380,verification_seconds=time.time()-start)
 (ROOT/'checkpoint_verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
