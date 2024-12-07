importScripts('https://www.gstatic.com/firebasejs/11.0.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.0.2/firebase-messaging-compat.js');

// ตั้งค่า Firebase
firebase.initializeApp({
    apiKey: "AIzaSyCmKxJerDOJc8hoQ7FrkA42RmjTwAg5B78",
    authDomain: "sit-to-fit-40890.firebaseapp.com",
    projectId: "sit-to-fit-40890",
    storageBucket: "sit-to-fit-40890.firebasestorage.app",
    messagingSenderId: "267449225965",
    appId: "1:267449225965:web:490cb8dcb99a97fdbdb2e4",
    measurementId: "G-YLTQJ1ZXPJ"
  });
const messaging = firebase.messaging();

// ฟังก์ชันที่ใช้ในการรับการแจ้งเตือน
messaging.onBackgroundMessage(function(payload) {
  console.log('Message received. ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: 'http://127.0.0.1:8000/static/images/logo.jpg'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
