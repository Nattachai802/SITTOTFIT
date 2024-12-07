from firebase_admin import credentials, messaging, initialize_app
import firebase_admin

# Initialize Firebase
cred = credentials.Certificate("Notification\key\sit-to-fit-40890-firebase-adminsdk-tt616-ee3b9a7e1d.json")
firebase_admin.initialize_app(cred)
print("Firebase initialized")

def send_multiple_notifications(registration_tokens, title, body):
    print("Running scheduled task...")
    """
    ส่ง Push Notification ไปยังหลาย Token พร้อมกัน
    """
    print(registration_tokens)
    if not registration_tokens:
        print("No registration tokens provided.")
        return None

    # Ensure registration_tokens is a list of strings (even if only one token is provided)
    if isinstance(registration_tokens, str):
        registration_tokens = [registration_tokens]
    


    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=registration_tokens[0]  
    )

    try:
        response = messaging.send(message)
        print(response)
        print(f"Successfully sent {response.success_count} messages.")
        print(f"Failed to send {response.failure_count} messages.")
        if response.failure_count > 0:
            for idx, error in enumerate(response.responses):
                if not error.success:
                    print(f"Failed to send to {registration_tokens[idx]}: {error.exception}")
        return response
    except Exception as e:
        print(f"Error sending notifications: {e}")
        return None
