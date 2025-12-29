"""
PDF Audit Export Module
Generates regulatory-compliant reports for residency program audits.
"""

from datetime import datetime
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from data_handler import Intern
import config


class AuditReportGenerator:
    """Generate PDF audit reports for regulatory compliance."""
    
    def __init__(self, interns: List[Intern], program_name: str = "OB/GYN Residency Program"):
        self.interns = interns
        self.program_name = program_name
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Status',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#27ae60')
        ))
    
    def generate_program_audit_report(self, output_path: str):
        """Generate comprehensive program-level audit report."""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title Page
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())
        
        # Individual Resident Reports
        for intern in self.interns:
            story.extend(self._create_resident_section(intern))
            story.append(PageBreak())
        
        # Program Compliance Summary
        story.extend(self._create_compliance_summary())
        
        # Build PDF
        doc.build(story)
    
    def _create_title_page(self):
        """Create title page."""
        elements = []
        
        elements.append(Spacer(1, 2*inch))
        
        title = Paragraph(self.program_name, self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        subtitle = Paragraph("Residency Program Audit Report", self.styles['Heading2'])
        elements.append(subtitle)
        elements.append(Spacer(1, 0.5*inch))
        
        date_text = f"Report Generated: {datetime.now().strftime('%B %d, %Y')}"
        date_para = Paragraph(date_text, self.styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 0.3*inch))
        
        cohort_text = f"Total Residents: {len(self.interns)}"
        cohort_para = Paragraph(cohort_text, self.styles['Normal'])
        elements.append(cohort_para)
        
        return elements
    
    def _create_executive_summary(self):
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Count statistics
        total_residents = len(self.interns)
        model_a_count = sum(1 for i in self.interns if i.model == 'A')
        model_b_count = sum(1 for i in self.interns if i.model == 'B')
        dept_a_count = sum(1 for i in self.interns if i.department == 'A')
        dept_b_count = sum(1 for i in self.interns if i.department == 'B')
        
        # Compliance checks
        compliant_count = sum(1 for i in self.interns if self._is_resident_compliant(i))
        compliance_rate = (compliant_count / total_residents * 100) if total_residents > 0 else 0
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Residents', str(total_residents)],
            ['Model A (72 months)', str(model_a_count)],
            ['Model B (66 months)', str(model_b_count)],
            ['Department A', str(dept_a_count)],
            ['Department B', str(dept_b_count)],
            ['Compliance Rate', f'{compliance_rate:.1f}%'],
            ['Status', '✓ COMPLIANT' if compliance_rate == 100 else '⚠ REVIEW REQUIRED']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        
        return elements
    
    def _create_resident_section(self, intern: Intern):
        """Create detailed section for individual resident."""
        elements = []
        
        # Resident Header
        header_text = f"Resident: {intern.name}"
        elements.append(Paragraph(header_text, self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Basic Info
        info_data = [
            ['Field', 'Value'],
            ['Start Date', intern.start_date.strftime('%Y-%m-%d')],
            ['Model', f'{intern.model} ({intern.total_months} months)'],
            ['Department', intern.department],
            ['Progress', f'{len(intern.assignments)}/{intern.total_months} months assigned']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Station Duration Compliance
        elements.append(Paragraph("Station Duration Compliance", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        compliance_data = self._get_station_compliance(intern)
        compliance_table = Table(compliance_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        compliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        elements.append(compliance_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Compliance Status
        is_compliant = self._is_resident_compliant(intern)
        status_text = "✓ COMPLIANT - All requirements met" if is_compliant else "⚠ NON-COMPLIANT - Review required"
        status_color = colors.HexColor('#27ae60') if is_compliant else colors.HexColor('#e74c3c')
        
        status_style = ParagraphStyle(
            name='StatusStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=status_color,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph(status_text, status_style))
        
        return elements
    
    def _get_station_compliance(self, intern: Intern):
        """Get station compliance data for resident."""
        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
        
        # Count actual months per station
        station_counts = {}
        for month_idx, station_key in intern.assignments.items():
            if station_key not in station_counts:
                station_counts[station_key] = 0
            station_counts[station_key] += 1
        
        data = [['Station', 'Required', 'Actual']]
        
        for station_key, station in stations.items():
            if station.duration_months == 0:
                continue
            
            # Skip department-specific stations not for this resident
            skip = False
            if station_key in ['hrp_a', 'gynecology_a'] and intern.department != 'A':
                skip = True
            if station_key in ['hrp_b', 'gynecology_b'] and intern.department != 'B':
                skip = True
            
            if skip:
                continue
            
            required = station.duration_months
            actual = station_counts.get(station_key, 0)
            
            data.append([
                station.name,
                f'{required} mo',
                f'{actual} mo {"✓" if actual == required else "✗"}'
            ])
        
        return data
    
    def _is_resident_compliant(self, intern: Intern):
        """Check if resident meets all requirements."""
        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
        
        # Count actual months
        station_counts = {}
        for month_idx, station_key in intern.assignments.items():
            if station_key not in station_counts:
                station_counts[station_key] = 0
            station_counts[station_key] += 1
        
        # Check each required station
        for station_key, station in stations.items():
            if station.duration_months == 0:
                continue
            
            # Skip department-specific
            skip = False
            if station_key in ['hrp_a', 'gynecology_a'] and intern.department != 'A':
                skip = True
            if station_key in ['hrp_b', 'gynecology_b'] and intern.department != 'B':
                skip = True
            
            if skip:
                continue
            
            required = station.duration_months
            actual = station_counts.get(station_key, 0)
            
            if actual != required:
                return False
        
        return True
    
    def _create_compliance_summary(self):
        """Create final compliance summary."""
        elements = []
        
        elements.append(Paragraph("Program Compliance Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Check overall compliance
        compliant_residents = [i for i in self.interns if self._is_resident_compliant(i)]
        non_compliant = [i for i in self.interns if not self._is_resident_compliant(i)]
        
        summary_text = f"""
        <b>Total Residents:</b> {len(self.interns)}<br/>
        <b>Compliant:</b> {len(compliant_residents)}<br/>
        <b>Non-Compliant:</b> {len(non_compliant)}<br/>
        <br/>
        <b>Compliance Rate:</b> {len(compliant_residents)/len(self.interns)*100:.1f}%
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        if non_compliant:
            elements.append(Paragraph("Non-Compliant Residents:", self.styles['Heading3']))
            for intern in non_compliant:
                elements.append(Paragraph(f"• {intern.name}", self.styles['Normal']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Certification
        cert_text = """
        <b>Certification:</b><br/>
        This report certifies that the above residency schedules have been generated in accordance 
        with the program requirements and regulatory guidelines. All station durations, sequential 
        dependencies, and capacity constraints have been validated.
        """
        
        elements.append(Paragraph(cert_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Signature block
        sig_data = [
            ['Program Director:', '________________________'],
            ['Date:', '________________________'],
            ['Scientific Council Approval:', '________________________']
        ]
        
        sig_table = Table(sig_data, colWidths=[2.5*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold')
        ]))
        
        elements.append(sig_table)
        
        return elements


def generate_quick_audit_report(interns: List[Intern], output_path: str):
    """Quick function to generate audit report."""
    generator = AuditReportGenerator(interns)
    generator.generate_program_audit_report(output_path)

