import os
import resend


def send_mail(recipient: str, subject: str, content: str):
    if os.getenv("EMAIL_TEST") == "True":
        print(f"Email content: {content}, Recipient: {recipient}")
    else:
        # Here you would add the actual email sending logic
        resend.api_key = os.environ["RESEND_API_KEY"]
        params: resend.Emails.SendParams = {
            "from": "Mail Pigeon <languagetutor@zacpaulson.dev>",
            "to": [recipient],
            "subject": subject,
            "html": content,
        }

        resend.Emails.send(params)


if __name__ == "__main__":
    send_mail("zpaulson001@gmail.com", "hello", "<h2>I hope this works 🤞</h2>")
