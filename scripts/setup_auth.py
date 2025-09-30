#!/usr/bin/env python3
"""
Authentication Setup Script for SOC Dashboard
Helps configure email server and test authentication methods
"""

import os
import sys
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from getpass import getpass

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def generate_secret_key():
    """Generate a secure random key"""
    return secrets.token_hex(32)

def test_smtp_connection(smtp_server, smtp_port, smtp_username, smtp_password, smtp_from):
    """Test SMTP server connection"""
    try:
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            print("✓ Connected to SMTP server")
            
            print("Starting TLS...")
            server.starttls()
            print("✓ TLS started")
            
            print(f"Logging in as {smtp_username}...")
            server.login(smtp_username, smtp_password)
            print("✓ Authentication successful")
            
            # Send test email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'SOC Dashboard - Email Configuration Test'
            msg['From'] = smtp_from
            msg['To'] = smtp_username
            
            text = "This is a test email from SOC Dashboard. Your email configuration is working correctly!"
            html = """
            <html>
              <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #3b82f6;">SOC Dashboard Email Test</h2>
                <p>Your email configuration is working correctly!</p>
                <p style="color: #666; font-size: 12px;">
                  If you received this email, your SMTP settings are properly configured.
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            print(f"Sending test email to {smtp_username}...")
            server.send_message(msg)
            print("✓ Test email sent successfully!")
            
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("  - For Gmail: Use an App Password, not your regular password")
        print("  - Enable 2-Factor Authentication first")
        print("  - Visit: https://myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Check your internet connection")
        print("  - Verify SMTP server and port are correct")
        print("  - Check if firewall is blocking SMTP")
        return False

def setup_gmail():
    """Guide user through Gmail setup"""
    print_header("Gmail Setup")
    
    print("To use Gmail for email OTP:")
    print("1. Enable 2-Factor Authentication on your Google account")
    print("2. Go to: https://myaccount.google.com/apppasswords")
    print("3. Generate an App Password for 'Mail'")
    print("4. Copy the 16-character password\n")
    
    email = input("Enter your Gmail address: ").strip()
    print("\nEnter your App Password (16 characters, spaces will be removed):")
    app_password = getpass("App Password: ").replace(" ", "")
    
    return {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': app_password,
        'SMTP_FROM': email
    }

def setup_outlook():
    """Guide user through Outlook setup"""
    print_header("Outlook/Office 365 Setup")
    
    email = input("Enter your Outlook/Office 365 email: ").strip()
    password = getpass("Enter your password: ")
    
    return {
        'SMTP_SERVER': 'smtp-mail.outlook.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': email,
        'SMTP_PASSWORD': password,
        'SMTP_FROM': email
    }

def setup_custom():
    """Guide user through custom SMTP setup"""
    print_header("Custom SMTP Setup")
    
    smtp_server = input("SMTP Server (e.g., smtp.example.com): ").strip()
    smtp_port = input("SMTP Port (usually 587 or 465): ").strip()
    smtp_username = input("SMTP Username: ").strip()
    smtp_password = getpass("SMTP Password: ")
    smtp_from = input("From Email Address: ").strip()
    
    return {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'SMTP_USERNAME': smtp_username,
        'SMTP_PASSWORD': smtp_password,
        'SMTP_FROM': smtp_from
    }

def setup_mailtrap():
    """Guide user through Mailtrap setup (for testing)"""
    print_header("Mailtrap Setup (Testing Only)")
    
    print("Mailtrap is a fake SMTP server for testing.")
    print("Emails won't actually be sent, but you can view them in Mailtrap.")
    print("\n1. Sign up at https://mailtrap.io")
    print("2. Get your SMTP credentials from the inbox settings\n")
    
    username = input("Mailtrap Username: ").strip()
    password = getpass("Mailtrap Password: ")
    
    return {
        'SMTP_SERVER': 'smtp.mailtrap.io',
        'SMTP_PORT': '2525',
        'SMTP_USERNAME': username,
        'SMTP_PASSWORD': password,
        'SMTP_FROM': 'test@soc-dashboard.local'
    }

def update_env_file(config):
    """Update or create .env file with configuration"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
    
    # Read existing .env or use .env.example as template
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    elif os.path.exists(env_example_path):
        with open(env_example_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update configuration
    updated_lines = []
    keys_updated = set()
    
    for line in lines:
        updated = False
        for key, value in config.items():
            if line.startswith(f"{key}="):
                updated_lines.append(f"{key}={value}\n")
                keys_updated.add(key)
                updated = True
                break
        if not updated:
            updated_lines.append(line)
    
    # Add any missing keys
    for key, value in config.items():
        if key not in keys_updated:
            updated_lines.append(f"{key}={value}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"\n✓ Configuration saved to {env_path}")

def main():
    """Main setup function"""
    print_header("SOC Dashboard - Authentication Setup")
    
    print("This script will help you configure authentication for the SOC Dashboard.")
    print("\nWhat would you like to set up?")
    print("1. Gmail (recommended for development)")
    print("2. Outlook/Office 365")
    print("3. Custom SMTP Server")
    print("4. Mailtrap (testing only)")
    print("5. Test existing configuration")
    print("6. Generate secret keys")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == '0':
        print("Goodbye!")
        return
    
    elif choice == '1':
        config = setup_gmail()
    
    elif choice == '2':
        config = setup_outlook()
    
    elif choice == '3':
        config = setup_custom()
    
    elif choice == '4':
        config = setup_mailtrap()
    
    elif choice == '5':
        print_header("Testing Existing Configuration")
        
        # Try to load from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            smtp_from = os.getenv('SMTP_FROM')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                print("✗ Missing SMTP configuration in .env file")
                print("Please run this script again to configure email settings.")
                return
            
            test_smtp_connection(smtp_server, smtp_port, smtp_username, smtp_password, smtp_from)
            
        except ImportError:
            print("✗ python-dotenv not installed. Install with: pip install python-dotenv")
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
        
        return
    
    elif choice == '6':
        print_header("Generate Secret Keys")
        
        flask_key = generate_secret_key()
        jwt_key = generate_secret_key()
        
        print("Generated secret keys:")
        print(f"\nFLASK_SECRET_KEY={flask_key}")
        print(f"JWT_SECRET_KEY={jwt_key}")
        
        print("\nAdd these to your .env file.")
        
        if input("\nUpdate .env file automatically? (y/n): ").lower() == 'y':
            update_env_file({
                'FLASK_SECRET_KEY': flask_key,
                'JWT_SECRET_KEY': jwt_key
            })
        
        return
    
    else:
        print("Invalid choice!")
        return
    
    # Test the configuration
    print_header("Testing Configuration")
    
    success = test_smtp_connection(
        config['SMTP_SERVER'],
        int(config['SMTP_PORT']),
        config['SMTP_USERNAME'],
        config['SMTP_PASSWORD'],
        config['SMTP_FROM']
    )
    
    if success:
        print("\n✓ Email configuration is working!")
        
        if input("\nSave configuration to .env file? (y/n): ").lower() == 'y':
            # Also generate secret keys if they don't exist
            if not os.getenv('FLASK_SECRET_KEY'):
                config['FLASK_SECRET_KEY'] = generate_secret_key()
                config['JWT_SECRET_KEY'] = generate_secret_key()
                print("\n✓ Generated new secret keys")
            
            update_env_file(config)
            
            print("\n" + "="*60)
            print("  Setup Complete!")
            print("="*60)
            print("\nNext steps:")
            print("1. Start MongoDB: mongod")
            print("2. Start the backend: python src/dashboard/server.py")
            print("3. Start the frontend: cd frontend && npm start")
            print("4. Open http://localhost:3000")
            print("\nFor more information, see AUTHENTICATION_SETUP.md")
    else:
        print("\n✗ Configuration test failed. Please check your settings and try again.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
