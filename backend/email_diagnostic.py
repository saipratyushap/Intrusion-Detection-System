#!/usr/bin/env python3
"""
Email Diagnostic Tool
Run this to diagnose email alert issues
"""

import sys
sys.path.insert(0, '/Users/psaipratyusha/Downloads/Intrusion-Detection-System-main 2/backend')

from email_service import EmailService
import smtplib
import ssl
from datetime import datetime

def diagnose_email():
    print("=" * 60)
    print("EMAIL ALERT DIAGNOSTIC TOOL")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Check configuration
    print("STEP 1: Checking Configuration")
    print("-" * 40)
    s = EmailService()
    
    print(f"✓ Email enabled: {s.config['enabled']}")
    print(f"✓ SMTP server: {s.config['smtp_server']}")
    print(f"✓ SMTP port: {s.config['smtp_port']}")
    print(f"✓ Sender email set: {bool(s.config['sender_email'])}")
    print(f"✓ Recipients configured: {len(s.config['recipient_emails'])}")
    print(f"✓ Recipients: {s.config['recipient_emails']}")
    
    if not s.config['enabled']:
        print("\n❌ ISSUE: Email service is DISABLED")
        print("   Fix: Set EMAIL_ENABLED=true in backend/.env")
        return
    
    if not s.config['sender_email']:
        print("\n❌ ISSUE: No sender email configured")
        print("   Fix: Set EMAIL_SENDER_EMAIL=your-email@gmail.com in backend/.env")
        return
    
    if not s.config['recipient_emails']:
        print("\n❌ ISSUE: No recipients configured")
        print("   Fix: Set EMAIL_RECIPIENT_EMAIL=recipient@gmail.com in backend/.env")
        return
    
    print()
    
    # Step 2: Test SMTP connection
    print("STEP 2: Testing SMTP Connection")
    print("-" * 40)
    
    try:
        context = ssl.create_default_context()
        
        print(f"Connecting to {s.config['smtp_server']}:{s.config['smtp_port']}...")
        
        if s.config['smtp_port'] == 465:
            with smtplib.SMTP_SSL(s.config['smtp_server'], s.config['smtp_port'], context=context, timeout=30) as server:
                print("✓ SMTP_SSL connection successful")
                print(f"Server response: {server.helo_resp.decode() if hasattr(server.helo_resp, 'decode') else server.helo_resp}")
        else:
            with smtplib.SMTP(s.config['smtp_server'], s.config['smtp_port'], timeout=30) as server:
                print("✓ SMTP connection successful")
                server.starttls(context=context)
                print("✓ TLS started successfully")
                print(f"Server response: {server.helo_resp.decode() if hasattr(server.helo_resp, 'decode') else server.helo_resp}")
        
        print()
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print("   This usually means:")
        print("   1. Wrong email or password")
        print("   2. For Gmail: Need an 'App Password', not regular password")
        print("   3. 2FA must be enabled to generate App Password")
        print()
        return
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ERROR: {e}")
        print()
        return
        
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {type(e).__name__}: {e}")
        print()
        return
    
    # Step 3: Test login
    print("STEP 3: Testing Authentication")
    print("-" * 40)
    
    try:
        context = ssl.create_default_context()
        
        if s.config['smtp_port'] == 465:
            with smtplib.SMTP_SSL(s.config['smtp_server'], s.config['smtp_port'], context=context, timeout=30) as server:
                server.login(s.config['sender_email'], s.config['sender_password'])
                print("✓ Login successful")
        else:
            with smtplib.SMTP(s.config['smtp_server'], s.config['smtp_port'], timeout=30) as server:
                server.starttls(context=context)
                server.login(s.config['sender_email'], s.config['sender_password'])
                print("✓ Login successful")
                
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ LOGIN FAILED: {e.smtp_error.decode() if hasattr(e, 'smtp_error') and hasattr(e.smtp_error, 'decode') else str(e)}")
        print()
        print("🔧 SOLUTION FOR GMAIL:")
        print("   1. Go to: https://myaccount.google.com/security")
        print("   2. Enable 2-Factor Authentication")
        print("   3. Go to: https://myaccount.google.com/apppasswords")
        print("   4. Create a new app password")
        print("   5. Use that 16-digit password in EMAIL_SENDER_PASSWORD")
        return
        
    except Exception as e:
        print(f"❌ LOGIN ERROR: {type(e).__name__}: {e}")
        return
    
    print()
    
    # Step 4: Send test email
    print("STEP 4: Sending Test Email")
    print("-" * 40)
    
    test_report = {
        'report_type': 'Diagnostic Test',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'summary': {
            'total_detections': 0,
            'total_violations': 0,
            'violation_rate': 0,
            'avg_confidence': 0
        },
        'kpis': {},
        'executive_summary': {
            'insights': ['This is a diagnostic test email'],
            'recommendations': ['If you received this, email is working!']
        }
    }


    result = s.send_report_email(test_report)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        print()
        print("=" * 60)
        print("✅ EMAIL SYSTEM IS WORKING CORRECTLY!")
        print("=" * 60)
        print()
        print("If alerts are still not coming, check:")
        print("1. Spam folder")
        print("2. API endpoints are being called correctly")
        print("3. Violations are being detected")
        print("4. Scheduled reports are running")
    else:
        print()
        print("=" * 60)
        print(f"❌ EMAIL SENDING FAILED: {result['message']}")
        print("=" * 60)



if __name__ == "__main__":
    diagnose_email()



