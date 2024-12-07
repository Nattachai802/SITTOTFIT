import firebase_admin
from firebase_admin import credentials, messaging

# ชี้ไปยังไฟล์ service account ที่คุณดาวน์โหลดมา
cred = credentials.Certificate(r"key/sit-to-fit-40890-firebase-adminsdk-tt616-ee3b9a7e1d.json")
firebase_admin.initialize_app(cred)

def send_single_notification(registration_token, title, body):
    # สร้าง message object
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=registration_token,
    )

    # ส่ง message
    response = messaging.send(message)
    print("Successfully sent message:", response)

# ตัวอย่างการใช้งาน
my_token = "e01P7B1h2sIJjmgE1urlOi:APA91bF30QinQ7X2lJ32w193aEvubyuxRap_yyMnyrtoFwOJ8RlU4OBTlLDiK7mBEThtdy_xAoLUoBYHegAsapbholVkYAOq3utCE8_3gUI-1XMk9xkikD4"
send_single_notification(my_token, "Hello!", "This is a test push notification")
