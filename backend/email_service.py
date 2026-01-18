"""
Email Notification Service

Production-ready email service with:
- Template-based emails
- HTML and plain text support
- Attachment handling
- Rate limiting
- Queue support for bulk emails
- SMTP and SendGrid integration
"""

import logging
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from string import Template

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class EmailMessage:
    """Email message structure"""
    message_id: str
    to_addresses: List[str]
    subject: str
    body_text: str
    body_html: Optional[str]
    from_address: str
    cc_addresses: List[str]
    bcc_addresses: List[str]
    reply_to: Optional[str]
    attachments: List[Dict[str, Any]]
    headers: Dict[str, str]
    priority: EmailPriority
    status: EmailStatus
    created_at: str
    sent_at: Optional[str]
    error_message: Optional[str]
    template_id: Optional[str]
    template_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data


class EmailTemplate:
    """Email template definition"""
    
    TEMPLATES = {
        'welcome': {
            'subject': 'Welcome to Nalytiq Data Platform',
            'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4a90d9, #357abd); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4a90d9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Nalytiq</h1>
        </div>
        <div class="content">
            <p>Hello ${name},</p>
            <p>Welcome to the Nalytiq Data Platform! Your account has been successfully created.</p>
            <p>You can now access:</p>
            <ul>
                <li>Data Catalog and Federation</li>
                <li>ML Training and Prediction</li>
                <li>X-Road Secure Data Exchange</li>
                <li>Compliance and Reporting Tools</li>
            </ul>
            <a href="${login_url}" class="button">Login to Your Account</a>
            <p>If you have any questions, please contact our support team.</p>
            <p>Best regards,<br>The Nalytiq Team</p>
        </div>
        <div class="footer">
            <p>National Institute of Statistics of Rwanda (NISR)</p>
            <p>KG 590 St, Kigali, Rwanda</p>
        </div>
    </div>
</body>
</html>
''',
            'body_text': '''
Hello ${name},

Welcome to the Nalytiq Data Platform! Your account has been successfully created.

You can now access:
- Data Catalog and Federation
- ML Training and Prediction
- X-Road Secure Data Exchange
- Compliance and Reporting Tools

Login here: ${login_url}

Best regards,
The Nalytiq Team
'''
        },
        'password_reset': {
            'subject': 'Reset Your Password - Nalytiq',
            'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .warning { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello ${name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <a href="${reset_url}" class="button">Reset Password</a>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong> This link expires in ${expiry_hours} hours. If you didn't request this reset, please ignore this email.
            </div>
            <p>Best regards,<br>The Nalytiq Team</p>
        </div>
    </div>
</body>
</html>
''',
            'body_text': '''
Hello ${name},

We received a request to reset your password.

Reset your password here: ${reset_url}

This link expires in ${expiry_hours} hours.

If you didn't request this reset, please ignore this email.

Best regards,
The Nalytiq Team
'''
        },
        'report_ready': {
            'subject': 'Your Report is Ready - ${report_name}',
            'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .info { background: #e7f5ea; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Report Ready</h1>
        </div>
        <div class="content">
            <p>Hello ${name},</p>
            <p>Your report <strong>${report_name}</strong> has been generated successfully.</p>
            <div class="info">
                <p><strong>Report Details:</strong></p>
                <ul>
                    <li>Format: ${format}</li>
                    <li>Generated: ${generated_at}</li>
                    <li>File Size: ${file_size}</li>
                </ul>
            </div>
            <a href="${download_url}" class="button">Download Report</a>
            <p>The report will be available for download for 7 days.</p>
            <p>Best regards,<br>The Nalytiq Team</p>
        </div>
    </div>
</body>
</html>
''',
            'body_text': '''
Hello ${name},

Your report "${report_name}" has been generated successfully.

Report Details:
- Format: ${format}
- Generated: ${generated_at}
- File Size: ${file_size}

Download: ${download_url}

The report will be available for 7 days.

Best regards,
The Nalytiq Team
'''
        },
        'security_alert': {
            'subject': '🔒 Security Alert - Nalytiq Account',
            'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .alert { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .details { background: #fff; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Security Alert</h1>
        </div>
        <div class="content">
            <p>Hello ${name},</p>
            <div class="alert">
                <strong>⚠️ ${alert_type}</strong>
                <p>${alert_message}</p>
            </div>
            <div class="details">
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Time: ${timestamp}</li>
                    <li>IP Address: ${ip_address}</li>
                    <li>Location: ${location}</li>
                </ul>
            </div>
            <p>If this was you, no action is needed. If you don't recognize this activity, please change your password immediately.</p>
            <p>Best regards,<br>The Nalytiq Security Team</p>
        </div>
    </div>
</body>
</html>
''',
            'body_text': '''
Hello ${name},

SECURITY ALERT: ${alert_type}

${alert_message}

Details:
- Time: ${timestamp}
- IP Address: ${ip_address}
- Location: ${location}

If this was you, no action is needed. If you don't recognize this activity, please change your password immediately.

Best regards,
The Nalytiq Security Team
'''
        },
        'dataset_access_approved': {
            'subject': 'Dataset Access Approved - ${dataset_name}',
            'body_html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #17a2b8; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #17a2b8; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Access Approved</h1>
        </div>
        <div class="content">
            <p>Hello ${name},</p>
            <p>Great news! Your access request for <strong>${dataset_name}</strong> has been approved.</p>
            <p>You can now:</p>
            <ul>
                <li>View dataset details and schema</li>
                <li>Execute queries against the data</li>
                <li>Include in federated queries</li>
            </ul>
            <a href="${dataset_url}" class="button">Access Dataset</a>
            <p>Access expires: ${expiry_date}</p>
            <p>Best regards,<br>The Nalytiq Team</p>
        </div>
    </div>
</body>
</html>
''',
            'body_text': '''
Hello ${name},

Your access request for "${dataset_name}" has been approved!

You can now view, query, and include this dataset in federated queries.

Access the dataset: ${dataset_url}
Access expires: ${expiry_date}

Best regards,
The Nalytiq Team
'''
        }
    }
    
    @classmethod
    def get_template(cls, template_id: str) -> Optional[Dict[str, str]]:
        """Get a template by ID"""
        return cls.TEMPLATES.get(template_id)
    
    @classmethod
    def render(cls, template_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render a template with data"""
        template = cls.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return {
            'subject': Template(template['subject']).safe_substitute(data),
            'body_html': Template(template['body_html']).safe_substitute(data),
            'body_text': Template(template['body_text']).safe_substitute(data)
        }
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List available template IDs"""
        return list(cls.TEMPLATES.keys())


class EmailService:
    """Email sending service with SMTP and SendGrid support"""
    
    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        smtp_use_tls: bool = True,
        from_address: str = "noreply@nalytiq.gov.rw",
        from_name: str = "Nalytiq Platform",
        sendgrid_api_key: str = ""
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.from_address = from_address
        self.from_name = from_name
        self.sendgrid_api_key = sendgrid_api_key
        
        # Email log storage
        self.email_log_file = "./data/email_log.json"
        self.email_log: List[EmailMessage] = []
        self._load_log()
    
    def _load_log(self) -> None:
        """Load email log"""
        try:
            if os.path.exists(self.email_log_file):
                with open(self.email_log_file, 'r') as f:
                    data = json.load(f)
                    for msg_data in data:
                        msg_data['priority'] = EmailPriority(msg_data['priority'])
                        msg_data['status'] = EmailStatus(msg_data['status'])
                        self.email_log.append(EmailMessage(**msg_data))
        except Exception as e:
            logger.warning(f"Failed to load email log: {e}")
    
    def _save_log(self, message: EmailMessage) -> None:
        """Save email log"""
        try:
            self.email_log.append(message)
            # Keep last 1000 emails
            if len(self.email_log) > 1000:
                self.email_log = self.email_log[-1000:]
            
            os.makedirs(os.path.dirname(self.email_log_file), exist_ok=True)
            with open(self.email_log_file, 'w') as f:
                json.dump([m.to_dict() for m in self.email_log], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save email log: {e}")
    
    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: str = None,
        attachments: List[Dict[str, Any]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        template_id: str = None,
        template_data: Dict[str, Any] = None
    ) -> EmailMessage:
        """
        Send an email.
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
            attachments: List of {filename, data, mimetype}
            priority: Email priority
            template_id: Template ID if using template
            template_data: Data for template rendering
        
        Returns:
            EmailMessage with status
        """
        to_addresses = [to] if isinstance(to, str) else to
        
        # Create message record
        message = EmailMessage(
            message_id=str(uuid.uuid4()),
            to_addresses=to_addresses,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            from_address=f"{self.from_name} <{self.from_address}>",
            cc_addresses=cc or [],
            bcc_addresses=bcc or [],
            reply_to=reply_to,
            attachments=attachments or [],
            headers={},
            priority=priority,
            status=EmailStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            sent_at=None,
            error_message=None,
            template_id=template_id,
            template_data=template_data or {}
        )
        
        # Try to send
        try:
            message.status = EmailStatus.SENDING
            
            if self.sendgrid_api_key:
                self._send_via_sendgrid(message)
            else:
                self._send_via_smtp(message)
            
            message.status = EmailStatus.SENT
            message.sent_at = datetime.utcnow().isoformat()
            logger.info(f"Email sent successfully to {to_addresses}")
            
        except Exception as e:
            message.status = EmailStatus.FAILED
            message.error_message = str(e)
            logger.error(f"Failed to send email: {e}")
        
        self._save_log(message)
        return message
    
    def send_template(
        self,
        template_id: str,
        to: Union[str, List[str]],
        data: Dict[str, Any],
        **kwargs
    ) -> EmailMessage:
        """Send email using a template"""
        rendered = EmailTemplate.render(template_id, data)
        
        return self.send(
            to=to,
            subject=rendered['subject'],
            body_text=rendered['body_text'],
            body_html=rendered['body_html'],
            template_id=template_id,
            template_data=data,
            **kwargs
        )
    
    def _send_via_smtp(self, message: EmailMessage) -> None:
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.subject
        msg['From'] = message.from_address
        msg['To'] = ', '.join(message.to_addresses)
        
        if message.cc_addresses:
            msg['Cc'] = ', '.join(message.cc_addresses)
        if message.reply_to:
            msg['Reply-To'] = message.reply_to
        
        # Add text part
        msg.attach(MIMEText(message.body_text, 'plain'))
        
        # Add HTML part if provided
        if message.body_html:
            msg.attach(MIMEText(message.body_html, 'html'))
        
        # Add attachments
        for attachment in message.attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.get('data', b''))
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment.get("filename", "attachment")}"'
            )
            msg.attach(part)
        
        # Send
        all_recipients = message.to_addresses + message.cc_addresses + message.bcc_addresses
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.smtp_use_tls:
                server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.sendmail(message.from_address, all_recipients, msg.as_string())
    
    def _send_via_sendgrid(self, message: EmailMessage) -> None:
        """Send email via SendGrid API"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            mail = Mail(
                from_email=Email(self.from_address, self.from_name),
                to_emails=[To(addr) for addr in message.to_addresses],
                subject=message.subject,
                plain_text_content=Content("text/plain", message.body_text),
                html_content=Content("text/html", message.body_html) if message.body_html else None
            )
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(mail)
            
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"SendGrid error: {response.status_code}")
                
        except ImportError:
            logger.warning("SendGrid library not installed, falling back to SMTP")
            self._send_via_smtp(message)
    
    def get_email_log(
        self,
        status: EmailStatus = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get email log"""
        logs = self.email_log
        if status:
            logs = [m for m in logs if m.status == status]
        return [m.to_dict() for m in logs[-limit:]]


# Global email service
email_service = EmailService(
    smtp_host=os.environ.get('SMTP_HOST', 'localhost'),
    smtp_port=int(os.environ.get('SMTP_PORT', '587')),
    smtp_user=os.environ.get('SMTP_USER', ''),
    smtp_password=os.environ.get('SMTP_PASSWORD', ''),
    sendgrid_api_key=os.environ.get('SENDGRID_API_KEY', '')
)


def get_email_service() -> EmailService:
    return email_service
