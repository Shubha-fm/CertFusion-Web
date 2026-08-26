from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def build_report(result: dict) -> bytes:
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=A4)
    w,h=A4; y=h-22*mm
    c.setFont('Helvetica-Bold',16); c.drawString(20*mm,y,'CertFusion Research Analysis Report'); y-=10*mm
    c.setFont('Helvetica',9); c.drawString(20*mm,y,f"Request ID: {result['request_id']}"); y-=6*mm
    c.drawString(20*mm,y,f"Execution mode: {result['mode']}"); y-=10*mm
    c.setFont('Helvetica-Bold',12); c.drawString(20*mm,y,'Prediction'); y-=7*mm
    c.setFont('Helvetica',10); c.drawString(20*mm,y,f"Class: {result['predicted_class']}"); y-=6*mm
    c.drawString(20*mm,y,f"Confidence: {result['confidence']*100:.1f}%"); y-=6*mm
    c.drawString(20*mm,y,f"Uncertainty: {result['uncertainty_level']} (entropy {result['entropy']:.3f})"); y-=6*mm
    c.drawString(20*mm,y,f"Conformal-like set: {', '.join(result['conformal_set'])}"); y-=10*mm
    c.setFont('Helvetica-Bold',12); c.drawString(20*mm,y,'Formal assurance'); y-=7*mm
    c.setFont('Helvetica',10); c.drawString(20*mm,y,f"Overall SMT status: {result['verification_status']}"); y-=6*mm
    c.drawString(20*mm,y,f"Rule satisfaction: {result['rule_satisfaction_rate']*100:.1f}%"); y-=10*mm
    for rr in result['rules']:
        if y < 35*mm: c.showPage(); y=h-20*mm
        c.setFont('Helvetica-Bold',9); c.drawString(20*mm,y,f"{rr['id']}  {rr['name']}"); y-=5*mm
        c.setFont('Helvetica',8); c.drawString(25*mm,y,f"Soft satisfaction {rr['satisfaction']*100:.1f}% | robust check {rr['robust_status']}"); y-=6*mm
    y-=3*mm
    c.setFont('Helvetica-Bold',10); c.drawString(20*mm,y,'Research-use disclaimer'); y-=6*mm
    c.setFont('Helvetica',8)
    text=c.beginText(20*mm,y); text.setLeading(4.2*mm)
    for line in result['disclaimer'].split('. '): text.textLine(line.strip())
    c.drawText(text); c.save(); return buf.getvalue()
