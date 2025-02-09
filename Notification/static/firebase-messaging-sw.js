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

let lastNotificationId = null;
let lastNotificationTime = 0;
const NOTIFICATION_THRESHOLD = 1000; // 1 วินาที

// ฟังก์ชันที่ใช้ในการรับการแจ้งเตือน
messaging.onBackgroundMessage(function(payload) {
    console.log('Message received in SW:', payload);
    
    const currentTime = Date.now();
    if (currentTime - lastNotificationTime < NOTIFICATION_THRESHOLD) {
        console.log('Skipping duplicate notification');
        return;
    }
    
    lastNotificationTime = currentTime;
    
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/images/logo.jpg',
        tag: currentTime.toString(),
        renotify: false,
        requireInteraction: false,
        silent: false,
        data: {
            notificationId: currentTime.toString()
        }
    };
    
    return self.registration.showNotification(
        payload.notification.title, 
        notificationOptions
    );
});

// จัดการกับการคลิก notification
self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event);
    event.notification.close();
    
    const urlToOpen = new URL('/', self.location.origin).href;
    
    const promiseChain = clients.matchAll({
        type: 'window',
        includeUncontrolled: true
    })
    .then((windowClients) => {
        for (let i = 0; i < windowClients.length; i++) {
            const client = windowClients[i];
            if (client.url === urlToOpen && 'focus' in client) {
                return client.focus();
            }
        }
        if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
        }
    });
    
    event.waitUntil(promiseChain);
});