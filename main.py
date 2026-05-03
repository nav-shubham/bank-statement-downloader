import imaplib
import email
from email.header import decode_header
import os
import re
from dotenv import load_dotenv

# ===== LOAD ENV =====
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

PROCESSED_FILE = "processed_emails.txt"

# ===== BANK CONFIG =====
BANK_CONFIGS = [
    {
        "name": "SVC",
        "sender": "noreply@svcbank.co.in",
        "label": '"Bank Statements/SVC"',
        "subject_keywords": ["statement"],
        "folder": "D:/03 Permanent Personal Data/01 Expences/Bank Statements"
    },
    {
        "name": "Kotak",
        "sender": "BankStatements@kotak.bank.in",
        "label": '"Bank Statements/Kotak"',
        "subject_keywords": ["statement"],
        "folder": "D:/03 Permanent Personal Data/01 Expences/Bank Statements"
    },
    {
        "name": "BOM",
        "sender": "mahaalert@mahabank.co.in",
        "label": '"Bank Statements/BOM"',
        "subject_keywords": ["statement"],
        "folder": "D:/03 Permanent Personal Data/01 Expences/Bank Statements"
    },
    {
        "name": "Paytm",
        "sender": "no-reply@paytm.com",
        "label": '"Bank Statements/Paytm"',
        "subject_keywords": ["statement"],
        "folder": "D:/03 Permanent Personal Data/01 Expences/UPI_Statements"
    }
]

# ================= HELPERS =================

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(f.read().splitlines())

def save_processed(eid):
    with open(PROCESSED_FILE, "a") as f:
        f.write(eid + "\n")

def clean_text(text):
    return "".join(c if c.isalnum() or c == "." else "_" for c in text)

def connect_mail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def search_emails(mail, sender, label):
    mail.select(label)
    status, messages = mail.search(None, f'(FROM "{sender}")')
    return messages[0].split()

def subject_matches(subject, keywords):
    subject = subject.lower()
    return any(k.lower() in subject for k in keywords)

def extract_date_from_subject(subject):
    patterns = [
        r'(\d{2})-([A-Za-z]{3})-(\d{4})',
        r'([A-Za-z]{3})-(\d{2,4})'
    ]
    for pattern in patterns:
        match = re.search(pattern, subject)
        if match:
            parts = match.groups()
            if len(parts) == 3:
                return f"{parts[1]}_{parts[2]}"
            elif len(parts) == 2:
                year = parts[1]
                if len(year) == 2:
                    year = "20" + year
                return f"{parts[0]}_{year}"
    return None

def get_extension(original_name):
    if original_name and "." in original_name:
        return original_name.split(".")[-1]
    return "pdf"

def fix_filename(filename):
    if not filename:
        filename = "statement.pdf"
    filename = clean_text(filename)
    if filename.lower().endswith("_pdf"):
        filename = filename[:-4] + ".pdf"
    if "." not in filename:
        filename += ".pdf"
    return filename

# ================= CORE =================

def download_attachments(mail, email_ids, bank, processed):
    bank_name = bank["name"]
    keywords = bank["subject_keywords"]
    if bank["name"] == "Paytm":
        folder = bank["folder"]  # direct folder (no subfolder)
    else:
        folder = os.path.join(bank["folder"], bank["name"])  # keep bank folders

    os.makedirs(folder, exist_ok=True)

    for eid in email_ids:
        eid_str = eid.decode()

        if eid_str in processed:
            continue

        res, msg_data = mail.fetch(eid, "(RFC822)")

        for response in msg_data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                #if not subject_matches(subject, keywords):
                #    continue

                print(f"Processing: {subject}")

                for part in msg.walk():
                    if part.get_content_disposition() == "attachment":

                        original_name = part.get_filename()
                        ext = get_extension(original_name)
                        date_part = extract_date_from_subject(subject)

                        if date_part:
                            filename = f"{bank_name}_{date_part}.{ext}"
                        else:
                            filename = fix_filename(original_name)

                        filepath = os.path.join(folder, filename)

                        if os.path.exists(filepath):
                            print(f"Skipped (exists): {filename}")
                            continue

                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        print(f"Downloaded: {filename}")

                save_processed(eid_str)

# ================= MAIN =================

def main():
    processed = load_processed()
    mail = connect_mail()

    for bank in BANK_CONFIGS:
        print(f"\nChecking {bank['name']}...")

        email_ids = search_emails(
            mail,
            bank["sender"],
            bank["label"]
        )

        download_attachments(mail, email_ids, bank, processed)

    mail.logout()

if __name__ == "__main__":
    main()
