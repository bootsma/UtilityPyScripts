import googlemaps
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import os
import smtplib
from email.message import EmailMessage
from cryptography.fernet import Fernet

# --- CONFIGURATION ---
KEY_FILE = "master.key"
ENCRYPTED_API_FILE = "api_key.enc"
ORIGIN = '610 University Avenue, Toronto, Ontario'
DESTINATION = '77 Little John Rd. Dundas, Ontario'
THRESHOLD_MIN = 45
INTERVAL = 300

# Email Settings
EMAIL_ON=False
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-app-password"
RECEIVER_EMAIL = "target-email@gmail.com"


# ---------------------

def get_or_set_api_key():
    """Handles encryption and retrieval of the API key."""
    # 1. Handle the Master Key (The 'Lock')
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()

    fernet = Fernet(key)

    # 2. Handle the API Key (The 'Secret')
    if not os.path.exists(ENCRYPTED_API_FILE):
        raw_api_key = input("No API key found. Please enter your Google Maps API Key: ").strip()
        encrypted_key = fernet.encrypt(raw_api_key.encode())
        with open(ENCRYPTED_API_FILE, "wb") as f:
            f.write(encrypted_key)
        print(f"API key encrypted and saved to {ENCRYPTED_API_FILE}")
        return raw_api_key
    else:
        with open(ENCRYPTED_API_FILE, "rb") as f:
            encrypted_data = f.read()
        return fernet.decrypt(encrypted_data).decode()


def send_alert(current_time):
    if not EMAIL_ON:
        return
    msg = EmailMessage()
    msg.set_content(f"Traffic Alert! Current travel time to {DESTINATION} is {current_time} minutes.")
    msg['Subject'] = '🚗 High Traffic Alert'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print("Alert email sent!")
    except Exception as e:
        print(f"Email failed: {e}")


def get_traffic_data(gmaps_client):
    result = gmaps_client.distance_matrix(
        ORIGIN, DESTINATION, mode='driving',
        departure_time='now', traffic_model='best_guess'
    )
    element = result['rows'][0]['elements'][0]
    if element['status'] == 'OK':
        duration_min = round(element['duration_in_traffic']['value'] / 60, 2)
        return {"time": datetime.now(), "duration": duration_min}
    return None


def generate_html(df):
    current = df.iloc[-1]['duration']
    trend = "➡️ Stable"
    if len(df) > 1:
        prev = df.iloc[-2]['duration']
        trend = "📈 Increasing" if current > prev else "📉 Decreasing" if current < prev else "➡️ Stable"

    fig = px.line(df, x='time', y='duration', title=f"Traffic: {ORIGIN} to {DESTINATION}")
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    html_content = f"""
    <html>
    <head><meta http-equiv="refresh" content="60">
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; padding: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; max-width: 900px; margin: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .status {{ font-size: 24px; font-weight: bold; color: {'red' if current > THRESHOLD_MIN else 'green'}; }}
    </style></head>
    <body>
        <div class="card">
            <h2>Route Monitor</h2>
            <div class="status">{current} min ({trend})</div>
            <p>Target Threshold: {THRESHOLD_MIN} min</p>
            {chart_html}
            <p><small>Last Update: {df.iloc[-1]['time'].strftime('%H:%M:%S')}</small></p>
        </div>
    </body></html>
    """
    with open("traffic_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)


# Initialize
API_KEY = get_or_set_api_key()
gmaps = googlemaps.Client(key=API_KEY)
data_history = []

print("Monitoring started. View results in traffic_report.html")

try:
    while True:
        entry = get_traffic_data(gmaps)
        if entry:
            data_history.append(entry)
            df = pd.DataFrame(data_history)
            generate_html(df)
            if entry['duration'] > THRESHOLD_MIN:
                send_alert(entry['duration'])
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Program terminated.")