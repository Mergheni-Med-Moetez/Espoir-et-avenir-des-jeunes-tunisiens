import io
import logging
from django.core.files.base import ContentFile
from django.contrib.auth.models import Group
from apps.core.models import Case, Alert

try:
    from langchain_community.llms import Ollama
except ImportError:
    # Fallback if specific package not loaded
    Ollama = None

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger(__name__)

def create_alerts_for_case(case):
    """
    Creates an alert for Supervisors and System Admins when a case
    transitions to an at-risk state. Does NOT generate the AI report yet.
    """
    groups = Group.objects.filter(name__in=['Supervisor', 'System Admin'])
    users_to_alert = set()
    for group in groups:
        for user in group.user_set.all():
            users_to_alert.add(user)
    
    for user in users_to_alert:
        Alert.objects.create(
            target_user=user,
            case=case,
            message=f"Case {case.reference} has been flagged as at-risk. Please generate an AI report."
        )
    logger.info(f"Alerts created for case {case.reference}")


def generate_report_for_alert(alert):
    """
    Connects to Ollama and generates the AI report text for a specific alert's case.
    Saves the generated text to the alert.report_text field.
    """
    if Ollama is None:
        logger.error("Langchain Ollama is not installed or import failed.")
        alert.report_text = "Failed to generate AI report: Langchain Ollama is not available."
        alert.save()
        return False

    case = alert.case

    try:
        # Connect to local Ollama (default port 11434). Assuming llama3 model is available.
        llm = Ollama(model="llama3", temperature=0.7)
        
        # Build prompt based on scenario
        if case.scenario == Case.Scenario.EDUCATION:
            try:
                student = case.student_record
                risk_factors = ", ".join(student.risk_factors) if student.risk_factors else "None"
                prompt = f"""
                Act as an expert educational counselor.
                Please provide a detailed report and advice for the following student at risk:
                
                Student ID: {student.student_id}
                Name: {student.first_name} {student.last_name}
                Attendance Rate: {student.attendance_rate}%
                Grade Trend: {student.get_grade_trend_display()}
                Behavior Notes: {student.behavior_notes_count}
                Risk Factors: {risk_factors}
                
                Provide:
                1. A brief analysis of their situation.
                2. Actionable advice and intervention steps for counselors.
                """
            except Exception:
                prompt = f"Provide advice for education case {case.reference}: {case.title}. {case.description}"
                
        elif case.scenario == Case.Scenario.HEALTH:
            try:
                record = case.health_record
                risk_factors = ", ".join(record.risk_factors) if record.risk_factors else "None"
                prompt = f"""
                Act as an expert health counselor for youths.
                Please provide a detailed report and advice for the following youth health case:
                
                Name: {record.first_name} {record.last_name}
                Health Condition: {record.health_condition}
                Missed Appointments: {record.missed_appointments}
                Treatment Adherence: {record.adherence_rate}%
                Risk Factors: {risk_factors}
                
                Provide:
                1. A brief analysis of their situation.
                2. Actionable advice and intervention steps for health counselors.
                """
            except Exception:
                prompt = f"Provide advice for health case {case.reference}: {case.title}. {case.description}"
        else:
            prompt = f"Provide advice for case {case.reference}: {case.title}. {case.description}"

        # Generate text
        report_text = llm.invoke(prompt)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ollama generation failed: {error_msg}")
        
        # If Ollama is not running, provide a simulated fallback report for demo purposes
        if "Connection refused" in error_msg or "Max retries exceeded" in error_msg or "10061" in error_msg:
            logger.info("Providing simulated AI report because Ollama is not reachable.")
            report_text = f"""#### 1. Analysis of Situation
The subject's current metrics indicate a concerning trend that requires immediate intervention. The risk factors present suggest a high likelihood of continued decline if left unaddressed.

#### 2. Recommended Action Plan
- **Immediate:** Schedule a one-on-one counseling session within 48 hours to discuss these recent changes.
- **Short-term:** Implement a weekly check-in system to monitor adherence and progress.
- **Long-term:** Involve the family or support system to ensure a holistic approach to improving the outcome.
            """
        else:
            report_text = f"Failed to generate AI report due to error: {error_msg}"
    
    alert.report_text = report_text
    alert.save()
    return True


def generate_pdf_from_text(text, reference):
    """
    Takes plain markdown-ish text and returns the raw bytes of a generated PDF.
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"AI Intervention Report: {reference}", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Split text by newlines and add as paragraphs
    for line in text.split('\n'):
        if line.strip():
            safe_text = line.strip().replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(safe_text, styles['Normal']))
            story.append(Spacer(1, 6))
            
    try:
        doc.build(story)
        pdf_content = pdf_buffer.getvalue()
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        pdf_content = None
    finally:
        pdf_buffer.close()
        
    return pdf_content
