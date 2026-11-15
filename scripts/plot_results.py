#!/usr/bin/env python3
"""Generate journal-ready 300-dpi plots from committed numeric results only.

No photographs or facial embeddings are accessed. All confidence intervals in
Figure 1 are marginal Student-t intervals for *individual method means*;
they are NOT intervals for paired method differences. The latter are BCa.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
METHODS=('B1','B2','B3','P1a','P1b','P2')
OFFSETS={'B1':(8,6),'B2':(8,-18),'B3':(8,8),'P1a':(8,-20),'P1b':(8,8),'P2':(10,-18)}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=ROOT/'output/figures')
    args=p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt
    summary={(r['method'],r['metric']):r for r in read_csv(ROOT/'results/summary.csv')}
    fig,ax=plt.subplots(figsize=(8,4.5),dpi=300)
    for m in METHODS:
        a=summary[(m,'arcface_cosine')]; b=summary[(m,'brisque')]
        x=float(b['mean']);y=float(a['mean'])
        xerr=[[x-float(b['ci95_lower'])],[float(b['ci95_upper'])-x]]
        yerr=[[y-float(a['ci95_lower'])],[float(a['ci95_upper'])-y]]
        ax.errorbar(x,y,xerr=xerr,yerr=yerr,fmt='o',capsize=3,markersize=7,linewidth=1)
        ax.annotate(f"{m} (n={a['n']})",(x,y),xytext=OFFSETS[m],textcoords='offset points',fontsize=10)
    ax.set_xlabel('Mean BRISQUE (lower indicates better image-statistical quality)')
    ax.set_ylabel('Mean ArcFace cosine similarity (higher is better)')
    ax.set_xlim(0,75);ax.set_ylim(.40,1.03)
    ax.grid(alpha=.3);ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(args.output_dir/'mean_arcface_vs_brisque.png',dpi=300,bbox_inches='tight')
    fig.savefig(args.output_dir/'mean_arcface_vs_brisque.svg',bbox_inches='tight')
    plt.close(fig)

    focal=read_csv(ROOT/'results/paired_focal_8.csv')
    for metric,suffix,label in (
      ('arcface_cosine','arcface','Mean paired ArcFace difference (A − B)'),
      ('brisque','brisque','Mean paired BRISQUE difference (A − B)')):
        rows=[r for r in focal if r['metric']==metric]
        fig,ax=plt.subplots(figsize=(8,4),dpi=300)
        for i,r in enumerate(rows):
            m=float(r['mean_difference_A_minus_B']);lo=float(r['bca95_lower']);hi=float(r['bca95_upper'])
            ax.errorbar(m,i,xerr=[[m-lo],[hi-m]],fmt='o',capsize=4)
        ax.set_yticks(list(range(len(rows))))
        ax.set_yticklabels([f"{r['method_A']} − {r['method_B']}" for r in rows])
        ax.axvline(0,linestyle='--',linewidth=1)
        ax.set_xlabel(label+'; bars: marginal 95% BCa intervals')
        ax.set_ylim(-.5,len(rows)-.5);ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(args.output_dir/f'paired_{suffix}_differences.png',dpi=300,bbox_inches='tight')
        plt.close(fig)
    print('Figures generated in',args.output_dir)

if __name__=='__main__':main()
