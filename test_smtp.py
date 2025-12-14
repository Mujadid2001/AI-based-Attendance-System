import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "mujadid2001@gmail.com"
SENDER_PASSWORD = "wlqn tkcz psnv vjdv"
RECEIVER_EMAIL = "mujadid2001@gmail.com"

print("Testing Gmail SMTP Connection...")
print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Sender: {SENDER_EMAIL}")
print()

try:
    # Create SMTP session
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("✓ TLS connection successful")
    
    # Login
    print("Logging in...")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    print("✓ Login successful")
    
    # Send test email
    print("\nSending test email...")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Email - SMTP Configuration"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    
    text = "This is a test email to verify SMTP is working correctly."
    html = """
    <html>
      <body>
        <h2>SMTP Test Email</h2>
        <p>This is a test email to verify SMTP is working correctly.</p>
        <p>If you received this, your Gmail credentials are correct!</p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    print("✓ Email sent successfully!")
    
    server.quit()
    print("\n✅ All tests passed! Your Gmail SMTP is working correctly.")
    print(f"\nCheck your email at {RECEIVER_EMAIL}")
    
except smtplib.SMTPAuthenticationError:
    print("\n❌ ERROR: Authentication failed!")
    print("Make sure you're using the Gmail app password, not your regular password")
    print("App password should be: wlqn tkcz psnv vjdv")
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP ERROR: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
