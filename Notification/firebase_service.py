from firebase_admin import credentials, messaging, initialize_app
import firebase_admin
import time

# Initialize Firebase
cred = credentials.Certificate(r"Notification\key\sit-to-fit-40890-firebase-adminsdk-tt616-ee3b9a7e1d.json")
firebase_admin.initialize_app(cred)
print("Firebase initialized")

def send_multiple_notifications(registration_tokens, title, body):
    print("Running scheduled task...")
    """
    ส่ง Push Notification ไปยังหลาย Token พร้อมกัน
    """
    if not registration_tokens:
        print("No registration tokens provided.")
        return None

    # แปลง single token เป็น list ถ้าจำเป็น
    if isinstance(registration_tokens, str):
        registration_tokens = [registration_tokens]
    
    success_count = 0
    failure_count = 0
    
    for token in registration_tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon='/static/images/logo.jpg',
                        tag=str(int(time.time() * 1000))  # ใช้ timestamp เป็น tag
                    ),
                    headers={
                        'Urgency': 'high'
                    }
                ),
                data={
                    'timestamp': str(int(time.time() * 1000))
                },
                token=token
            )
            
            response = messaging.send(message)
            print(f"Successfully sent to token: {token}")
            success_count += 1
            
        except Exception as e:
            print(f"Failed to send to token {token}: {e}")
            failure_count += 1
    
    print(f"Completed sending notifications:")
    print(f"Success: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Total: {len(registration_tokens)}")
    
    return success_count > 0
