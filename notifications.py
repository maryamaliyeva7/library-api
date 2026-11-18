OUTBOX_PATH = "outbox.txt"


def send_email(email, subject, body):
    with open(OUTBOX_PATH, "a") as f:
        f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")