// Service Worker for Web Push Notifications
self.addEventListener('push', function(event) {
    console.log('Push event received:', event);
    
    if (event.data) {
        try {
            const data = event.data.json();
            console.log('Push data:', data);
            
            const options = {
                body: data.message || 'Stock Analysis Complete',
                icon: '/static/icon-192x192.png',
                badge: '/static/badge-72x72.png',
                vibrate: [100, 50, 100],
                data: data.data || {},
                requireInteraction: true, // Keep notification visible
                tag: 'stock-analysis', // Group notifications
                actions: [
                    {
                        action: 'view',
                        title: 'View Results'
                    },
                    {
                        action: 'dismiss',
                        title: 'Dismiss'
                    }
                ]
            };
            
            console.log('Showing notification with options:', options);
            
            event.waitUntil(
                self.registration.showNotification(data.title || 'Stock Analysis Alert', options)
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
                self.registration.showNotification('Stock Analysis Complete', {
                    body: 'Your stock analysis report is ready!',
                    requireInteraction: true
                })
            );
        }
    } else {
        console.log('No data in push event, showing default notification');
        event.waitUntil(
            self.registration.showNotification('Stock Analysis Complete', {
                body: 'Your stock analysis report is ready!',
                requireInteraction: true
            })
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the dashboard
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

self.addEventListener('notificationclose', function(event) {
    console.log('Notification closed:', event);
});

// Handle background sync for offline functionality
self.addEventListener('sync', function(event) {
    console.log('Background sync event:', event);
    
    if (event.tag === 'stock-analysis-sync') {
        event.waitUntil(
            // Handle offline sync when connection is restored
            console.log('Syncing stock analysis data...')
        );
    }
});

// Handle installation
self.addEventListener('install', function(event) {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

// Handle activation
self.addEventListener('activate', function(event) {
    console.log('Service Worker activating...');
    event.waitUntil(
        clients.claim()
    );
}); 