#!/usr/bin/env python3
"""
Audit Data Export Utility for SOC Dashboard
Supports multiple export formats with filtering and date range options
"""

import os
import json
import csv
import io
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd

class AuditExporter:
    """Handles export of audit data in various formats"""
    
    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        self.styles = getSampleStyleSheet()
        
        # Custom styles for PDF
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12
        )
    
    def export_audit_data(self, 
                         format_type: str = 'json',
                         start_date: str = None,
                         end_date: str = None,
                         event_type: str = None,
                         username: str = None,
                         severity: str = None,
                         include_summary: bool = True) -> Union[str, bytes]:
        """
        Export audit data in specified format
        
        Args:
            format_type: 'json', 'csv', 'pdf', or 'excel'
            start_date: ISO format date string
            end_date: ISO format date string
            event_type: Filter by specific event type
            username: Filter by username
            severity: Filter by severity level
            include_summary: Include summary statistics
            
        Returns:
            Exported data as string or bytes
        """
        
        # Get filtered audit data
        audit_data = self._get_filtered_audit_data(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            username=username,
            severity=severity
        )
        
        # Generate summary if requested
        summary = None
        if include_summary:
            summary = self._generate_export_summary(audit_data, start_date, end_date)
        
        # Export based on format
        if format_type.lower() == 'json':
            return self._export_json(audit_data, summary)
        elif format_type.lower() == 'csv':
            return self._export_csv(audit_data, summary)
        elif format_type.lower() == 'pdf':
            return self._export_pdf(audit_data, summary)
        elif format_type.lower() == 'excel':
            return self._export_excel(audit_data, summary)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _get_filtered_audit_data(self, 
                                start_date: str = None,
                                end_date: str = None,
                                event_type: str = None,
                                username: str = None,
                                severity: str = None) -> List[Dict]:
        """Get filtered audit data"""
        
        # Get all audit logs with basic filters
        result = self.audit_logger.get_audit_logs(
            page=1,
            per_page=10000,  # Get all records
            event_type=event_type,
            username=username,
            start_date=start_date,
            end_date=end_date
        )
        
        logs = result.get('logs', []) if isinstance(result, dict) else result
        
        # Apply additional severity filtering if needed
        if severity:
            logs = self._filter_by_severity(logs, severity)
        
        return logs
    
    def _filter_by_severity(self, logs: List[Dict], severity: str) -> List[Dict]:
        """Filter logs by severity level"""
        severity_mapping = {
            'high': ['account_locked', 'unauthorized_access', 'user_deleted', 'system_error'],
            'medium': ['login_failed', 'permission_denied', 'mfa_failed', 'password_changed'],
            'low': ['login_success', 'logout', 'alert_flagged', 'alert_dismissed']
        }
        
        target_events = severity_mapping.get(severity.lower(), [])
        if not target_events:
            return logs
        
        return [log for log in logs if log.get('event_type') in target_events]
    
    def _generate_export_summary(self, logs: List[Dict], start_date: str = None, end_date: str = None) -> Dict:
        """Generate summary statistics for export"""
        
        if not logs:
            return {
                'total_events': 0,
                'date_range': f"{start_date or 'N/A'} to {end_date or 'N/A'}",
                'event_types': {},
                'users': {},
                'success_rate': 0
            }
        
        # Count events by type
        event_counts = {}
        user_counts = {}
        success_count = 0
        total_count = len(logs)
        
        for log in logs:
            event_type = log.get('event_type', 'unknown')
            username = log.get('username', 'unknown')
            success = log.get('success', True)
            
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            user_counts[username] = user_counts.get(username, 0) + 1
            
            if success:
                success_count += 1
        
        # Calculate date range
        if logs:
            timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
            if timestamps:
                actual_start = min(timestamps)
                actual_end = max(timestamps)
                date_range = f"{actual_start} to {actual_end}"
            else:
                date_range = f"{start_date or 'N/A'} to {end_date or 'N/A'}"
        else:
            date_range = f"{start_date or 'N/A'} to {end_date or 'N/A'}"
        
        return {
            'total_events': total_count,
            'date_range': date_range,
            'event_types': event_counts,
            'users': user_counts,
            'success_rate': round((success_count / total_count) * 100, 2) if total_count > 0 else 0,
            'export_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _export_json(self, logs: List[Dict], summary: Dict = None) -> str:
        """Export audit data as JSON"""
        
        export_data = {
            'metadata': {
                'export_format': 'json',
                'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                'total_records': len(logs)
            },
            'audit_logs': logs
        }
        
        if summary:
            export_data['summary'] = summary
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_csv(self, logs: List[Dict], summary: Dict = None) -> str:
        """Export audit data as CSV"""
        
        if not logs:
            return "No audit data to export"
        
        # Prepare CSV data
        output = io.StringIO()
        
        # Write summary if provided
        if summary:
            output.write("# AUDIT EXPORT SUMMARY\n")
            output.write(f"# Total Events: {summary['total_events']}\n")
            output.write(f"# Date Range: {summary['date_range']}\n")
            output.write(f"# Success Rate: {summary['success_rate']}%\n")
            output.write(f"# Export Time: {summary['export_timestamp']}\n")
            output.write("\n")
        
        # Write CSV headers and data
        fieldnames = ['id', 'timestamp', 'event_type', 'username', 'ip_address', 
                     'user_agent', 'success', 'error_message', 'details']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in logs:
            # Flatten details for CSV
            row = {key: log.get(key, '') for key in fieldnames}
            if isinstance(row['details'], dict):
                row['details'] = json.dumps(row['details'])
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_excel(self, logs: List[Dict], summary: Dict = None) -> bytes:
        """Export audit data as Excel file"""
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Create main data sheet
            if logs:
                df = pd.DataFrame(logs)
                
                # Flatten details column
                if 'details' in df.columns:
                    df['details'] = df['details'].apply(
                        lambda x: json.dumps(x) if isinstance(x, dict) else str(x)
                    )
                
                df.to_excel(writer, sheet_name='Audit_Logs', index=False)
            
            # Create summary sheet if provided
            if summary:
                summary_data = []
                summary_data.append(['Metric', 'Value'])
                summary_data.append(['Total Events', summary['total_events']])
                summary_data.append(['Date Range', summary['date_range']])
                summary_data.append(['Success Rate', f"{summary['success_rate']}%"])
                summary_data.append(['Export Time', summary['export_timestamp']])
                summary_data.append(['', ''])
                
                # Event type breakdown
                summary_data.append(['Event Type', 'Count'])
                for event_type, count in summary['event_types'].items():
                    summary_data.append([event_type, count])
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
        
        output.seek(0)
        return output.getvalue()
    
    def _export_pdf(self, logs: List[Dict], summary: Dict = None) -> bytes:
        """Export audit data as PDF"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        title = Paragraph("SOC Dashboard - Audit Log Export", self.title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Export info
        export_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        info_text = f"<b>Export Date:</b> {export_time}<br/><b>Total Records:</b> {len(logs)}"
        story.append(Paragraph(info_text, self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Summary section
        if summary:
            story.append(Paragraph("Summary Statistics", self.heading_style))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Events', str(summary['total_events'])],
                ['Date Range', summary['date_range']],
                ['Success Rate', f"{summary['success_rate']}%"]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Event type breakdown
            if summary.get('event_types'):
                story.append(Paragraph("Event Type Breakdown", self.heading_style))
                
                event_data = [['Event Type', 'Count']]
                for event_type, count in summary['event_types'].items():
                    event_data.append([event_type, str(count)])
                
                event_table = Table(event_data)
                event_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(event_table)
                story.append(PageBreak())
        
        # Audit logs section
        if logs:
            story.append(Paragraph("Audit Log Details", self.heading_style))
            
            # Create table with limited columns for PDF readability
            table_data = [['Timestamp', 'Event Type', 'Username', 'Success', 'IP Address']]
            
            for log in logs[:100]:  # Limit to first 100 records for PDF
                timestamp = log.get('timestamp', '')[:19]  # Truncate timestamp
                event_type = log.get('event_type', '')
                username = log.get('username', '')[:20]  # Truncate long usernames
                success = 'Yes' if log.get('success', True) else 'No'
                ip_address = log.get('ip_address', '')[:15]  # Truncate IP
                
                table_data.append([timestamp, event_type, username, success, ip_address])
            
            # Create table
            audit_table = Table(table_data, repeatRows=1)
            audit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(audit_table)
            
            if len(logs) > 100:
                story.append(Spacer(1, 12))
                note = Paragraph(f"<i>Note: Only first 100 records shown. Total records: {len(logs)}</i>", 
                               self.styles['Normal'])
                story.append(note)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def get_export_filename(self, format_type: str, start_date: str = None, end_date: str = None) -> str:
        """Generate appropriate filename for export"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if start_date and end_date:
            date_part = f"_{start_date[:10]}_to_{end_date[:10]}"
        else:
            date_part = f"_{timestamp}"
        
        return f"soc_audit_export{date_part}.{format_type.lower()}"
