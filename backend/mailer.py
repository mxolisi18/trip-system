

def send_email(to_address: str, subject: str, body: str):
    # import inside function to avoid circular import during CLI/migrations
    from flask import current_app
    # placeholder for an actual mailer; logs to app logger for now
    current_app.logger.info(f"SEND EMAIL to={to_address} subject={subject} body={body}")
