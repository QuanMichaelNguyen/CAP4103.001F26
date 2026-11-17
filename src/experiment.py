"""Reproducible biometric authentication experiments for CAP4103.

This evaluates *simulated paired identities*, NOT actual cheating detection.
Use --mode real with the public datasets to obtain reportable results.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import fetch_olivetti_faces
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from src.hw3_evaluation import evaluate_with_hw3

SEED = 4103


def read_keystrokes(path: Path):
    """Load CMU DSL-StrongPasswordData.csv, or compatible CSV.

    Columns: subject, sessionIndex, rep, followed by numeric H./DD./UD. timings.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Download DSL-StrongPasswordData.csv from https://www.cs.cmu.edu/~keystroke/ and pass --keystroke-csv.")
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError('Keystroke CSV is empty')
    columns = [c for c in rows[0] if c.startswith(('H.', 'DD.', 'UD.'))]
    if not columns or 'subject' not in rows[0]:
        raise ValueError('Expected CMU benchmark columns: subject and timing features H./DD./UD.')
    samples = {}
    for row in rows:
        try:
            vec = np.array([float(row[c]) for c in columns], dtype=float)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(vec).all():
            continue
        samples.setdefault(row['subject'], []).append(vec)
    return {k: np.array(v) for k, v in sorted(samples.items())}


def load_real(path: Path, n_users: int, seed: int):
    faces = fetch_olivetti_faces(shuffle=False, download_if_missing=False)
    face_dict = {str(i): faces.data[faces.target == i] for i in np.unique(faces.target)}
    keys = read_keystrokes(path)
    rng = np.random.default_rng(seed)
    fids = sorted(face_dict)
    kids = sorted(k for k in keys if len(keys[k]) >= 10)
    n = min(n_users, len(fids), len(kids))
    if n < 3:
        raise ValueError('At least three users needed in each modality')
    # Pair independently sampled people as a *simulation*, not real shared identities.
    fids = [fids[i] for i in rng.permutation(len(fids))[:n]]
    kids = [kids[i] for i in rng.permutation(len(kids))[:n]]
    mapping = [{'simulated_user':i,'face_subject':fids[i], 'keystroke_subject':kids[i]} for i in range(n)]
    return {i:face_dict[fids[i]] for i in range(n)}, {i:keys[kids[i]] for i in range(n)}, mapping


def load_demo(n=12, seed=SEED):
    """DEMONSTRATION ONLY: generated data may not be used as empirical results."""
    rng = np.random.default_rng(seed)
    center_f = rng.normal(0, 2, (n, 64))
    center_k = rng.normal(0, 2, (n, 31))
    return ({i:center_f[i]+rng.normal(0,.75,(10,64)) for i in range(n)},
            {i:center_k[i]+rng.normal(0,1.5,(80,31)) for i in range(n)},
            [{'simulated_user':i,'face_subject':f'demo_face_{i}', 'keystroke_subject':f'demo_key_{i}'} for i in range(n)])


def split_data(data, seed=SEED):
    """Subject-stratified sample split; no probe sample appears in enrollment."""
    out={'enroll':{},'val':{},'test':{}}
    rng=np.random.default_rng(seed)
    for user, samples in data.items():
        idx=rng.permutation(len(samples))
        if len(idx)<6:
            raise ValueError('Need at least six samples per subject')
        n_enroll=max(2,int(len(idx)*.5)); n_val=max(1,int(len(idx)*.2))
        if n_enroll+n_val>=len(idx):
            raise ValueError('No test samples left')
        for label, chosen in [('enroll',idx[:n_enroll]),('val',idx[n_enroll:n_enroll+n_val]),('test',idx[n_enroll+n_val:])]:
            out[label][user]=samples[chosen]
    return out


class Matcher:
    def __init__(self, data, use_pca=False):
        enroll=np.concatenate(list(data.values()),axis=0)
        self.scaler=StandardScaler().fit(enroll)
        norm=self.scaler.transform(enroll)
        self.pca = PCA(n_components=min(60,len(norm)-1,norm.shape[1]),random_state=SEED).fit(norm) if use_pca else None
        self.templates={u:self.project(a).mean(axis=0) for u,a in data.items()}
    def project(self,a):
        x=self.scaler.transform(a)
        return self.pca.transform(x) if self.pca is not None else x
    def score(self, a, claimed):
        x=self.project(a)
        return -np.linalg.norm(x-self.templates[claimed],axis=1)


def score_claims(matcher, probes):
    """One genuine and N-1 impostor comparisons per probe (same fixed protocol)."""
    labels=[]; scores=[]
    for actual, samples in sorted(probes.items()):
        for claimed in sorted(matcher.templates):
            vals=matcher.score(samples,claimed)
            scores.extend(vals.tolist())
            labels.extend([int(actual==claimed)]*len(vals))
    return np.asarray(labels,dtype=int),np.asarray(scores,dtype=float)


def rates(labels,scores):
    """Equal-error estimate by minimizing abs(FAR - FRR) over score thresholds."""
    genuine=scores[labels==1]; impostor=scores[labels==0]
    if not len(genuine) or not len(impostor):
        raise ValueError('Need genuine and impostor trials')
    cuts=np.r_[np.inf, np.unique(scores)[::-1], -np.inf]
    far=np.array([(impostor >= t).mean() for t in cuts])
    frr=np.array([(genuine < t).mean() for t in cuts])
    idx=np.argmin(np.abs(far-frr))
    eer=float((far[idx]+frr[idx])/2)
    spread=np.sqrt((np.var(genuine)+np.var(impostor))/2)
    dprime=float(abs(np.mean(genuine)-np.mean(impostor))/spread) if spread>0 else float('inf')
    return {'eer':eer,'d_prime':dprime,'far_at_eer':float(far[idx]),'frr_at_eer':float(frr[idx]), 'threshold':float(cuts[idx])}


def normalize(scores, ref):
    std=np.std(ref)
    return (scores-np.mean(ref))/(std if std>1e-10 else 1.)


def plot_scores(labels,scores,title,path):
    plt.figure(figsize=(7,4))
    plt.hist(scores[labels==1],bins=30,alpha=.6,density=True,label='Genuine')
    plt.hist(scores[labels==0],bins=30,alpha=.6,density=True,label='Impostor')
    plt.xlabel('Similarity score (higher = better match)');plt.ylabel('Density')
    plt.title(title);plt.legend();plt.tight_layout();plt.savefig(path,dpi=160);plt.close()


def evaluate(face,key,output:Path, seed=SEED):
    output.mkdir(parents=True,exist_ok=True)
    if set(face)!=set(key):
        raise ValueError('Face and keystroke user IDs must match')
    fa=split_data(face,seed); ka=split_data(key,seed)
    fm=Matcher(fa['enroll'],use_pca=True);km=Matcher(ka['enroll'])
    val_f,svf=score_claims(fm,fa['val']);val_k,svk=score_claims(km,ka['val'])
    test_f,stf=score_claims(fm,fa['test']);test_k,stk=score_claims(km,ka['test'])
    # Different samples per modality: align trials by (actual, claimed) and
    # average probe scores per identity claim; do not pretend samples sync in time.
    def aggregate(matcher,partition):
        labels=[]; ss=[]
        for actual,samples in sorted(partition.items()):
            for claimed in sorted(matcher.templates):
                labels.append(int(actual==claimed))
                ss.append(float(np.mean(matcher.score(samples,claimed))))
        return np.array(labels),np.array(ss)
    vf,af=aggregate(fm,fa['val']); vk,ak=aggregate(km,ka['val'])
    tf,bf=aggregate(fm,fa['test']); tk,bk=aggregate(km,ka['test'])
    assert np.array_equal(vf,vk) and np.array_equal(tf,tk)
    zaf=normalize(af,af); zak=normalize(ak,ak)
    zbf=normalize(bf,af); zbk=normalize(bk,ak)
    out={'protocol':{'n_users':len(face),'trial_unit':'mean of held-out probes per (actual, claimed) identity',
                     'note':'Artificial cross-dataset identity pairing; not contemporaneous biometric capture'},
         'rq1':{'face':rates(test_f,stf),'keystroke':rates(test_k,stk)},'rq2':{},'rq3':{}}
    for weight in [0.,.25,.5,.75,1.]:
        zval=weight*zaf+(1-weight)*zak
        ztest=weight*zbf+(1-weight)*zbk
        out['rq3'][str(weight)]={'validation':rates(vf,zval),'test':rates(tf,ztest)}
    out['rq2']={'face_only':rates(tf,zbf),'keystroke_only':rates(tk,zbk),'equal_weight_fusion':out['rq3']['0.5']['test']}
    # Course-required HW3 Evaluator: actual held-out trials, no fabricated scores.
    # The HW3 implementation expects normalized [0,1] scores; calibration is
    # learned exclusively from the corresponding validation partition.
    out['hw3'] = {
        'rq1_face': evaluate_with_hw3(test_f, stf, svf, 'RQ1_Face', output, plots=True),
        'rq1_keystroke': evaluate_with_hw3(test_k, stk, svk, 'RQ1_Keystroke', output, plots=True),
        'rq2_face_only': evaluate_with_hw3(tf, zbf, zaf, 'RQ2_Face', output),
        'rq2_keystroke_only': evaluate_with_hw3(tk, zbk, zak, 'RQ2_Keystroke', output),
        'rq2_equal_fusion': evaluate_with_hw3(tf, .5*zbf+.5*zbk, .5*zaf+.5*zak,
                                              'RQ2_EqualFusion', output, plots=True),
    }

    best=min([0.,.25,.5,.75,1.],key=lambda w:out['rq3'][str(w)]['validation']['eer'])
    out['rq3']['selected_weight_from_validation']=best
    out['rq3']['selected_test']=out['rq3'][str(best)]['test']
    out['hw3']['rq3_selected_fusion'] = evaluate_with_hw3(
        tf, best*zbf+(1-best)*zbk, best*zaf+(1-best)*zak,
        'RQ3_SelectedFusion', output, plots=True)
    out['hw3']['rq3_selected_weight'] = float(best)
    plot_scores(test_f,stf,'RQ1: Face similarity',output/'face_scores.png')
    plot_scores(test_k,stk,'RQ1: Keystroke similarity',output/'keystroke_scores.png')
    plot_scores(tf,.5*zbf+.5*zbk,'RQ2: Equal-weight fused similarity',output/'fusion_scores.png')
    plt.figure(figsize=(7,4)); ws=[0.,.25,.5,.75,1.]
    plt.plot(ws,[out['rq3'][str(w)]['validation']['eer'] for w in ws],'o-',label='Validation EER')
    plt.plot(ws,[out['rq3'][str(w)]['test']['eer'] for w in ws],'s--',label='Test EER (not used for selection)')
    plt.xlabel('Face fusion weight');plt.ylabel('Equal-error rate');plt.legend();plt.tight_layout()
    plt.savefig(output/'fusion_weights.png',dpi=160);plt.close()
    (output/'metrics.json').write_text(json.dumps(out,indent=2,allow_nan=False))
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['real','demo'],default='real')
    ap.add_argument('--keystroke-csv',type=Path,default=Path('data/DSL-StrongPasswordData.csv'))
    ap.add_argument('--n-users',type=int,default=40)
    ap.add_argument('--output',type=Path,default=Path('results'))
    args=ap.parse_args()
    if args.mode=='real':
        try: f,k,m=load_real(args.keystroke_csv,args.n_users,SEED)
        except (FileNotFoundError, OSError) as e:
            ap.error(str(e)+'\nDownload Olivetti faces once using fetch_olivetti_faces(download_if_missing=True) on an internet-connected machine.')
    else:f,k,m=load_demo(min(args.n_users,12))
    args.output.mkdir(exist_ok=True,parents=True)
    (args.output/'identity_mapping.json').write_text(json.dumps(m,indent=2))
    summary=evaluate(f,k,args.output)
    summary['data_status']='DEMO_SYNTHETIC_NOT_REPORTABLE' if args.mode=='demo' else 'REAL_PUBLIC_DATASETS_SIMULATED_PAIRING'
    (args.output/'metrics.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
