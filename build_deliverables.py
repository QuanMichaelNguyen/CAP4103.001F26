"""Generate course submission drafts. Do not fabricate experimental results."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt as PPTPt
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT=Path(__file__).resolve().parent
PRESENTATION_TEMPLATE=ROOT/'templates'/'Biometrics_Presentation_Template.pptx'
REPORT_TEMPLATE=ROOT/'templates'/'MB_ReportTemplate.docx'

slides=Presentation(PRESENTATION_TEMPLATE)
texts={
 0:{0:'CAP4103 Mobile Biometrics | Fall 2026',1:'Exam Identity Verification with Face and Keystroke Biometrics',2:'Team: [insert five names]  •  Experimental project',3:'November 2026  |  Research results pending dataset execution'},
 1:{3:'Face vs. typing: which modality better separates genuine and impostor identity claims?',5:'Does equal-weight score fusion improve on either modality alone?',7:'Can validation-selected fusion weights improve combined authentication?'},
 2:{3:'Olivetti Faces: 40 people × 10 photos (AT&T Cambridge). CMU Keystroke Benchmark: 51 typists × 400 fixed-password samples. Use 40 matched simulated IDs.',5:'Seed 4103. Map 40 people from each independent dataset into simulated identities. Split each identity: ~50% enrollment / ~20% validation / remainder test. No cross-split probe reuse.',7:'Face: enrollment-trained PCA + Euclidean matching. Keystrokes: standardized timing features + Euclidean matching. Normalize validation score scale; combine by weighted score fusion.'},
 3:{2:'How do individual face and keystroke matchers compare?',4:'Separate enrollment templates, genuine and impostor claims; compare EER, d-prime, score distributions on held-out probes.',6:'RESULTS PENDING: run real public datasets. Report actual EER / d-prime for face and keystroke; do not use synthetic demo values.',8:'RQ2 tests whether these different biometric signals provide complementary evidence.',9:'INSERT: results/face_scores.png and results/keystroke_scores.png AFTER REAL RUN'},
 4:{2:'Does equal-weight score-level fusion outperform either modality?',4:'Identity-level mean probe scores; normalize using validation-set statistics; compare face-only, typing-only, and 50/50 fusion.',6:'RESULTS PENDING: fill EER and d-prime from results/metrics.json (rq2) after a real run.',8:'RQ3 investigates how changing the fusion weight affects validation and test errors.',9:'INSERT: results/fusion_scores.png AFTER REAL RUN'},
 5:{2:'How does the face/typing fusion weight affect accuracy?',4:'Compare face weights 0, .25, .5, .75, 1.0. Select by validation EER only; report the locked test result.',6:'RESULTS PENDING: list weight selected from validation and compare its held-out EER to equal fusion.',8:'The selected weight informs the proposed identity verification threshold; no automated cheating verdict is supported.',9:'INSERT: results/fusion_weights.png AFTER REAL RUN'},
 6:{3:'System implements three evaluable comparisons, but performance claims must await real-dataset execution. A mismatch is NOT proof of cheating.',5:'Artificial identity pairing, fixed-password typing, small face sample sizes, no live exam monitoring or liveness detection; RQ1 and RQ2 differ in trial unit.',7:'Risk: sensitive biometric templates and false accusations. Safeguards: permitted research datasets, minimized local storage, restricted access, human review of mismatches. See NIST and ISO/IEC 24745.'},
 7:{2:'Research framing: “Does combining independent biometric signals improve identity verification?” Not “Can we prove someone cheated?”'},
 8:{3:'Olivetti Faces / AT&T Cambridge: https://cam-orl.co.uk/facedatabase.html/\nCMU Benchmark: https://www.cs.cmu.edu/~keystroke/',5:'Killourhy & Maxion (2009), DOI: 10.1109/DSN.2009.5270346\nNIST FRTE demographic effects: https://pages.nist.gov/frvt/html/frvt_demographics.html\nISO/IEC 24745:2022: https://www.iso.org/standard/75302.html'}
}
for si, replacements in texts.items():
    s=slides.slides[si]
    for idx, val in replacements.items():
        sh=s.shapes[idx]
        if not sh.has_text_frame:continue
        sh.text=val
        for p in sh.text_frame.paragraphs:
            p.font.size=PPTPt(15 if idx not in (1,0) else (22 if idx==1 else 13))
# Visibly mark all research result slides as drafts.
slides.save(ROOT/'presentation'/'CAP4103_Exam_Authentication_DRAFT.pptx')

# Start from provided report template, retaining its section styles/layout framework.
doc=Document(REPORT_TEMPLATE)
body=doc._element.body
for child in list(body):
    if child.tag.endswith('sectPr'):continue
    body.remove(child)
sec=doc.sections[0];sec.top_margin=Inches(1);sec.bottom_margin=Inches(1);sec.left_margin=Inches(1);sec.right_margin=Inches(1)
normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1
normal.paragraph_format.space_after=Pt(5)

def para(txt,style=None):
    p=doc.add_paragraph(style=style)
    p.add_run(txt)
    p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def heading(s):
    p=doc.add_paragraph(style='Heading 1');p.add_run(s)
    p.style.font.name='Calibri';p.style.font.size=Pt(14);p.style.font.bold=True
    return p

title=doc.add_paragraph(style='Title');title.add_run('Multimodal Identity Verification for Online Exam Authentication')
title.alignment=WD_ALIGN_PARAGRAPH.CENTER
for r in title.runs:r.font.name='Calibri';r.font.size=Pt(14);r.bold=True
p=para('CAP4103 • Fall 2026 • Team: [insert names] • Draft protocol — empirical results pending')
for r in p.runs:r.italic=True
heading('Research Questions')
para('RQ1. How does the performance of facial recognition compare with keystroke dynamics when distinguishing genuine users from impostors? This establishes independent modality baselines.')
para('RQ2. Does equal-weight score-level fusion improve identity verification relative to either modality independently? This tests whether RQ1 modalities provide complementary evidence.')
para('RQ3. How does changing the relative weighting of face and keystroke scores affect authentication performance? The final question refines the fusion tested in RQ2; the final design should be revisited when prior experiments are observed.')
heading('Methodology')
para('Datasets. The AT&T/Olivetti faces corpus contains 40 individuals with 10 grayscale images each. The Carnegie Mellon University keystroke benchmark contains 51 typists with 400 repeated fixed-password typing samples each. Randomly select 40 typists and pair them with the 40 face subjects as simulated identities using seed 4103. These pairs are not actual records from the same person; no claim of joint real-world capture is made. Data must be acquired separately under applicable dataset permissions.')
para('Partition and features. Within each identity and modality, split samples using deterministic per-user shuffling into approximately 50% enrollment, 20% validation, and the remainder for test. Fit preprocessing solely to enrollment data. Train PCA on standardized facial pixels and form face identity templates from enrollment sample means. Standardize CMU key-hold and inter-key timing values and form enrollment typing templates. Negative Euclidean distance to a claimed-identity template is the similarity score (larger means closer).')
para('Experimental design. For RQ1, score every held-out probe against every claimed identity, producing genuine and impostor scores. For RQ2 and RQ3, average probe scores by (actual user, claimed user) separately within each modality before pairing identity-claim scores; this avoids treating distinct facial images and typing repetitions as simultaneous measurements. Standardize modality scores using validation distribution statistics. Fuse with S = w × S_face + (1 − w) × S_keystroke. RQ2 uses w = 0.5; RQ3 compares w ∈ {0, 0.25, 0.5, 0.75, 1.0}, selects by validation EER alone, and evaluates the chosen weight on held-out test data. Distinct RQ1 versus fusion trial units limit direct interpretation of comparisons.')
para('Evaluation and reproducibility. Report EER, d-prime, FAR/FRR at an empirical crossing threshold, and genuine/impostor score distribution plots. Use Python, NumPy, scikit-learn, and Matplotlib; fix seed at 4103. The original HW3 Evaluator is included unchanged, and called on real held-out genuine/impostor trials after validation-only score calibration to [0,1]. HW3-reported metrics and score-distribution/DET/ROC plots are generated automatically. Its fixed-threshold EER estimate is reported alongside the independent empirical-threshold estimate. Source code, dependencies, dataset instructions, and repeatable CLI calls are included in the repository package.')
heading('Results and Analysis')
t=doc.add_table(rows=1,cols=4);t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
for c,v in zip(t.rows[0].cells,['Experiment','Comparison','EER','d-prime']):c.text=v
for vals in [('RQ1','Face alone','PENDING','PENDING'),('RQ1','Keystroke alone','PENDING','PENDING'),('RQ2','Equal-weight fusion','PENDING','PENDING'),('RQ3','Selected validation weight','PENDING','PENDING')]:
    for c,v in zip(t.add_row().cells,vals):c.text=v
para('Table 1. Results placeholders. Populate exclusively from a completed --mode real run. Synthetic demo data verifies code paths only and cannot support a scientific conclusion.',style='Caption')
para('RQ1. The comparison is designed to identify which unimodal matcher better separates genuine and impostor attempts. RESULT PENDING: insert observed EER and d-prime for both modalities, discuss score distributions, and use the finding to motivate fusion.')
para('RQ2. The equal-weight fusion experiment will determine whether combining two different signals lowers EER and/or improves d-prime on identity-level claims relative to each identity-level unimodal baseline. RESULT PENDING: record values from metrics.json and interpret the direction and size of any change.')
para('RQ3. Validation-set EER will select a face weight from five prespecified options. The selected test EER is then reported once; selecting the best weight from test data would invalidate the comparison. RESULT PENDING: give the selected weight, validation EER, and locked test EER, with the weight-versus-EER plot.')
heading('Ethics Statement')
para('Faces and typing rhythms are sensitive biometric characteristics. An authentication mismatch can occur because of lighting, input devices, fatigue, or individual variation; it does not prove academic misconduct. Face recognition can also exhibit differential error rates across populations and image quality conditions (NIST, 2019). Such a system must not automatically assign cheating penalties based on these scores.')
para('The project uses historical public research datasets, not actual exam sessions. Artificially pairing different people across modalities supports a classroom fusion experiment but cannot establish real-world exam monitoring accuracy, fairness, or fraud detection capability. The fixed-password keystroke dataset likewise does not capture free-form typing during an exam (Killourhy & Maxion, 2009).')
para('Implemented research safeguards include local-only processing, published acquisition links instead of redistribution, a documented random mapping, reproducible splits, and no real student surveillance. A deployed system would additionally require informed consent, restrictive retention, access control, protected biometric templates, human review of alerts, and bias auditing consistent with biometric information protection guidance (ISO/IEC 24745:2022). These deployment safeguards have not been implemented in this experiment.')
doc.add_page_break()
heading('References')
for ref in [
 'AT&T Laboratories Cambridge. (n.d.). The Database of Faces. https://cam-orl.co.uk/facedatabase.html/',
 'Killourhy, K. S., & Maxion, R. A. (2009). Comparing anomaly-detection algorithms for keystroke dynamics. Proceedings of DSN 2009, 125–134. https://doi.org/10.1109/DSN.2009.5270346',
 'National Institute of Standards and Technology. (2019). Face Recognition Vendor Test: Demographic effects (NISTIR 8280). https://pages.nist.gov/frvt/html/frvt_demographics.html',
 'International Organization for Standardization. (2022). ISO/IEC 24745:2022: Biometric information protection. https://www.iso.org/standard/75302.html',
]:para(ref)
doc.save(ROOT/'report'/'CAP4103_Exam_Authentication_DRAFT.docx')
print('Generated draft report and slides')
