from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'comparison.csv').open()))
models=['tfidf_word_logreg','tfidf_char_logreg','distilbert_full_finetuning_1epoch']
labels=['Word TF-IDF','Character TF-IDF','DistilBERT · 1 epoch']
splits=['synthetic_test','public_holdout','hard_negative_challenge']
xticks=['Synthetic test\nn=100','Public emails\nn=100','Paired challenge\nn=80; 40 benign']
colors=['#7988a3','#51a49e','#5e50aa']
fig,axes=plt.subplots(1,2,figsize=(11,4.6))
x=np.arange(3);width=.24
for ax,metric,title in zip(axes,['f1','false_positive_rate'],['Phishing F1 · higher is better','Benign false-positive rate · lower is better']):
 for i,(model,label,color) in enumerate(zip(models,labels,colors)):
  values=[float(next(r for r in rows if r['split']==s and r['baseline']==model)[metric]) for s in splits]
  bars=ax.bar(x+(i-1)*width,values,width,label=label,color=color)
  for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v+.018,f'{v:.2f}',ha='center',va='bottom',fontsize=8)
 ax.set_xticks(x,xticks);ax.set_ylim(0,1.12);ax.set_title(title,fontsize=11);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.18)
 ax.spines[['top','right']].set_visible(False)
fig.suptitle('Same 800 synthetic training emails · fixed one-epoch all-layer DistilBERT',fontsize=12,y=.99)
handles,names=axes[0].get_legend_handles_labels();fig.legend(handles,names,ncol=3,loc='lower center',bbox_to_anchor=(.5,.01),frameon=False)
fig.text(.5,.105,'One seed; source-confounded public labels; authored challenge. No significance or deployment-safety claim.',ha='center',fontsize=8,color='#555555')
fig.tight_layout(rect=(0,.15,1,.94));fig.savefig(root/'benchmark.png',dpi=180,bbox_inches='tight');plt.close(fig)
