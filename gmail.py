from email.message import EmailMessage

import time
import secrets
import smtplib
import ssl 
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

sender_email = ""
sender_app_password = ""

receiver_email = sender_email

LCD_ADDR = 0x3f
lcd = CharLCD ("PCF8574", LCD_ADDR, port =1, cols =16, rows =2)
def show(line1:str, line2:str = "")
lcd.clear()
lcd.write_string(line1[:16])
lcd.cursor_pos = (1,0)
lcd.write_string(line2[:16])

def send_code_to_email(code:str):
    msg = EmailMessage()
    msg["from"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Your Rasberry Pi Access Code"
    msg.set_content(f"Your access code is {code}\n\nType this on the keypad to unlock.")
    with smtplib.SMTP("smtp.gmail.com", 587) as sever:
        server.starttls(context = context)
        server.login(sender_email, sender_app_password)
        server.send_message(msg)


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
green_led = 18
GPIO.setup(green_led, GPIO.OUT, initial = GPIO.LOW)
ROWS = [5,6,13,19]
COLS = [12,16,20, 21]
KEYS = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"],
]

# Row pins: outputs (we turn one row on at a time)
for r in ROWS:
    GPIO.setup(r, GPIO.OUT, initial=GPIO.LOW)

# Column pins: inputs with internal pull-down resistors
for c in COLS:
    GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def get_key_held():
    for i, r in enumerate(ROWS):
        GPIO.output(r, GPIO.HIGH)

        for j, c in enumerate(COLS):
            if GPIO.input(c) == 1:
                GPIO.output(r, GPIO.LOW)
                return KEYS[i][j]

        GPIO.output(r, GPIO.LOW)

    return None


# This makes it possible to press the same number twice (11, 22, etc.)
key_was_down = False

def get_new_keypress():
        global key_was_down

    k = get_key_held()

    # New press = key exists AND was not down before
    if k is not None and not key_was_down:
        key_was_down = True
        return k

    # If no key is held, reset
    if k is None:
        key_was_down = False

    return None

def collect_code(max_len=6):
    typed = ""

    while True:
        k = get_new_keypress()
        if k is None:
            time.sleep(0.03)
            continue

        if k == "*":  # backspace
            typed = typed[:-1]

        elif k == "#":  # submit
            return typed
        elif k.isdigit():  # numbers only
            if len(typed) < max_len:
                typed += k

        # Update LCD second line with stars
        lcd.cursor_pos = (1, 0)
        lcd.write_string(" " * 16)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(("*" * len(typed))[:16])

try:
    otp = "".join(str(secrets.randbelow(10)) for i in range(6))

    show("SENDING", "PASSWORD...")
    send_code_to_email(otp)

    show("ENTER CODE:", "")
    user_code = collect_code(max_len=6)

    if user_code == otp:
        show("ACCESS", "GRANTED")
    else:
        show("ACCESS", "DENIED")

    time.sleep(5)

finally:
    lcd.clear()
    GPIO.cleanup()