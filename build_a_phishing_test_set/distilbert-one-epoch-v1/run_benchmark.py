#!/usr/bin/env python3
"""One-epoch, all-layer DistilBERT fine-tuning; original synthetic train, three holdouts.
Fixed CPU-budget baseline, not the paper's three-epoch training protocol.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
import argparse, csv, hashlib, json, platform, time
from pathlib import Path

MODEL='distilbert/distilbert-base-uncased'
REVISION='12040accade4e8a0f71eabdb258fecc2e7e948be'
SEED=172289201

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--input',default=str(Path(__file__).resolve().parent/'dataset.jsonl'))
 ap.add_argument('--out',default=str(Path(__file__).resolve().parent/'results'))
 ap.add_argument('--cache-dir',default=None)
 ap.add_argument('--allow-cpu',action='store_true')
 ap.add_argument('--resume',action='store_true')
 args=ap.parse_args()
 import numpy as np
 import torch,transformers,accelerate,sklearn
 from transformers import AutoTokenizer,AutoModelForSequenceClassification,DataCollatorWithPadding,Trainer,TrainingArguments,set_seed,TrainerCallback
 from transformers.trainer_utils import get_last_checkpoint
 from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix
 source=Path(args.input);root=Path(args.out);root.mkdir(parents=True,exist_ok=True)
 expected=json.loads((Path(__file__).resolve().parent/'run_contract.json').read_text())
 digest=hashlib.sha256(source.read_bytes()).hexdigest()
 assert digest==expected['input_sha256'],'Input bytes differ from the fixed benchmark contract.'
 rows=[json.loads(l) for l in source.read_text().splitlines()]
 counts={s:sum(r['split']==s for r in rows) for s in ['train','validation','test','public_holdout','hard_negative_challenge']}
 assert counts=={'train':800,'validation':100,'test':100,'public_holdout':100,'hard_negative_challenge':80}
 if not torch.cuda.is_available() and not args.allow_cpu:
  raise SystemExit('No CUDA device. No training started. Use dedicated GPU compute, or explicitly pass --allow-cpu for a potentially hours-long run.')
 device='cuda' if torch.cuda.is_available() else 'cpu'
 set_seed(SEED);torch.set_num_threads(4)
 tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,cache_dir=args.cache_dir)
 model=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REVISION,num_labels=2,cache_dir=args.cache_dir,id2label={0:'non_phishing',1:'phishing'},label2id={'non_phishing':0,'phishing':1},attn_implementation='sdpa')
 assert all(p.requires_grad for p in model.parameters())
 class Emails(torch.utils.data.Dataset):
  def __init__(self,items):
   self.rows=items
   self.enc=tokenizer([r['email_text'] for r in items],truncation=True,max_length=512,padding=False)
  def __len__(self):return len(self.rows)
  def __getitem__(self,i):return {**{k:v[i] for k,v in self.enc.items()},'labels':self.rows[i]['phishing_label']}
 datasets={s:Emails([r for r in rows if r['split']==s]) for s in counts}
 config=TrainingArguments(output_dir=str(root/'checkpoints'),num_train_epochs=1,learning_rate=5e-5,weight_decay=.01,per_device_train_batch_size=8,gradient_accumulation_steps=2,per_device_eval_batch_size=4,eval_strategy='epoch',save_strategy='steps',save_steps=10,save_total_limit=1,load_best_model_at_end=False,logging_steps=5,report_to=[],seed=SEED,data_seed=SEED,use_cpu=device=='cpu',fp16=False,bf16=False,dataloader_num_workers=0,disable_tqdm=True)
 provenance=dict(status='training',input_sha256=digest,model=MODEL,revision=REVISION,seed=SEED,device=device,gpu_name=torch.cuda.get_device_name(0) if device=='cuda' else None,training_rows=800,validation_rows=100,test_rows=100,public_holdout_rows=100,trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),method='Full all-layer fine-tuning, float32; fixed ONE epoch, not paper three epochs; no test selection.',effective_batch_size=16,microbatch=8,gradient_accumulation=2,max_tokens=512,epochs=1,learning_rate=5e-5,weight_decay=.01,versions=dict(python=platform.python_version(),torch=torch.__version__,transformers=transformers.__version__,accelerate=accelerate.__version__,sklearn=sklearn.__version__,numpy=np.__version__))
 (root/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 class Progress(TrainerCallback):
  def on_step_end(self,args,state,control,**kwargs):
   status=dict(status='training',step=state.global_step,total_steps=state.max_steps,epoch=state.epoch,updated_unix=time.time())
   (root/'progress.json').write_text(json.dumps(status,indent=2)+'\n')
   if state.global_step%5==0:print(json.dumps(status),flush=True)
  def on_save(self,args,state,control,**kwargs):print('Resumable checkpoint saved at step '+str(state.global_step),flush=True)
 trainer=Trainer(model=model,args=config,train_dataset=datasets['train'],eval_dataset=datasets['validation'],data_collator=DataCollatorWithPadding(tokenizer=tokenizer),processing_class=tokenizer,callbacks=[Progress()])
 checkpoint=get_last_checkpoint(str(root/'checkpoints')) if args.resume and (root/'checkpoints').exists() else None
 if args.resume and checkpoint is None:raise SystemExit('--resume requested but no resumable checkpoint exists.')
 start=time.time();trainer.train(resume_from_checkpoint=checkpoint);training_seconds=time.time()-start
 # Holdout labels are only scored AFTER the fixed one-epoch run.
 scores=[];predictions=[]
 for split in ['validation','test','public_holdout','hard_negative_challenge']:
  print('Scoring '+split,flush=True)
  logits=trainer.predict(datasets[split]).predictions;p=logits.argmax(-1);y=np.array([r['phishing_label'] for r in datasets[split].rows])
  prob=torch.softmax(torch.tensor(logits),dim=-1)[:,1].numpy();tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
  scores.append(dict(split=split,baseline='distilbert_full_finetuning_1epoch',n=len(y),accuracy=float(accuracy_score(y,p)),precision=float(precision_score(y,p,zero_division=0)),recall=float(recall_score(y,p,zero_division=0)),f1=float(f1_score(y,p,zero_division=0)),false_positive_rate=float(fp/(fp+tn)),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp)))
  for r,guess,q in zip(datasets[split].rows,p,prob):predictions.append(dict(id=r['id'],split=split,gold=r['phishing_label'],prediction=int(guess),phishing_probability=float(q)))
 for name,data in [('distilbert_scores.csv',scores),('predictions.csv',predictions)]:
  with (root/name).open('w',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
 trainer.save_model(str(root/'final_model'));tokenizer.save_pretrained(str(root/'final_model'))
 (root/'training_history.json').write_text(json.dumps(trainer.state.log_history,indent=2)+'\n')
 provenance.update(status='completed',training_seconds=training_seconds,hard_negative_rows=80,threads=4,truncation_counts={s:sum(len(tokenizer(r['email_text'],truncation=False)['input_ids'])>512 for r in d.rows) for s,d in datasets.items()})
 (root/'progress.json').write_text(json.dumps({'status':'completed','step':50,'total_steps':50},indent=2)+'\n')
 (root/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print(json.dumps(scores,indent=2))

if __name__=='__main__':main()
