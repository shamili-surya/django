import streamlit as st
import requests

st.title("📧 Send Mail UI")

subject = st.text_input("Subject")
body = st.text_area("Body")
to_email = st.text_input("To Email (comma-separated)")

access_token = st.text_input("Paste JWT Token")

if st.button("Send Mail"):
    if not access_token:
        st.warning("JWT token is required")
    else:
        payload = {
            "subject": subject,
            "body": body,
            "to": [e.strip() for e in to_email.split(',')],
            "cc": [],
            "bcc": [],
            "is_draft": False
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post("http://127.0.0.1:8000/api/send-mail/", json=payload, headers=headers)

        if res.status_code == 201:
            st.success("✅ Mail sent successfully!")
        else:
            try:
                error_message = res.json().get('message', 'Unknown error')
            except ValueError:
                error_message = res.text 
                st.error(f"❌ Failed: {error_message}")

