// Service Worker for Web Push Notifications
self.addEventListener('push', function(event) {
    console.log('Push event received:', event);
    
    if (event.data) {
        try {
            const data = event.data.json();
            console.log('Push data:', data);
            
            const options = {
                body: data.message || 'Trading Alert',
                icon: '/icon-192x192.png',
                badge: '/badge-72x72.png',
                vibrate: [100, 50, 100],
                data: data.data || {},
                requireInteraction: true, // Keep notification visible
                tag: 'trading-alert', // Group notifications
                actions: [
                    {
                        action: 'view',
                        title: 'View Details'
                    },
                    {
                        action: 'dismiss',
                        title: 'Dismiss'
                    }
                ]
            };
            
            console.log('Showing notification with options:', options);
            
            event.waitUntil(
                self.registration.showNotification(data.title || 'Trading Alert', options)
                    .then(() => {
                        console.log('Notification shown successfully');
                    })
                    .catch((error) => {
                        console.error('Error showing notification:', error);
                    })
            );
        } catch (error) {
            console.error('Error processing push data:', error);
            // Show a fallback notification
            event.waitUntil(
                self.registration.showNotification('Trading Alert', {
                    body: 'New trading notification received',
                    requireInteraction: true
                })
            );
        }
    } else {
        console.log('No data in push event, showing default notification');
        event.waitUntil(
            self.registration.showNotification('Trading Alert', {
                body: 'New trading notification received',
                requireInteraction: true
            })
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the trading dashboard
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

self.addEventListener('pushsubscriptionchange', function(event) {
    console.log('Push subscription changed:', event);
    // Handle subscription renewal if needed
}); 