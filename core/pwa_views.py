from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)


def manifest(request):
    """Generate PWA manifest file"""
    manifest_data = {
        "name": "Apartment Management System",
        "short_name": "ApartmentMS",
        "description": "Modern apartment management system",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/images/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["productivity", "utilities"],
        "lang": "tr-TR",
        "dir": "ltr"
    }
    
    return JsonResponse(manifest_data, content_type='application/manifest+json')


def service_worker(request):
    """Generate service worker for PWA"""
    sw_content = """
const CACHE_NAME = 'apartment-management-v1';
const urlsToCache = [
  '/',
  '/static/css/app.min.css',
  '/static/js/app.js',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png',
  '/dashboard/',
  '/offline.html'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Push notification handling
self.addEventListener('push', function(event) {
  const options = {
    body: event.data ? event.data.text() : 'New notification',
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View',
        icon: '/static/images/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/images/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Apartment Management', options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'explore') {
    clients.openWindow('/dashboard/');
  } else if (event.action === 'close') {
    // Just close the notification
  }
});
"""
    
    return HttpResponse(sw_content, content_type='application/javascript')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def subscribe_push_notifications(request):
    """Subscribe user to push notifications"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        p256dh = data.get('keys', {}).get('p256dh')
        auth = data.get('keys', {}).get('auth')
        
        # Save subscription to database
        from .models import PushSubscription
        subscription, created = PushSubscription.objects.get_or_create(
            user=request.user,
            defaults={
                'endpoint': endpoint,
                'p256dh_key': p256dh,
                'auth_key': auth
            }
        )
        
        if not created:
            subscription.endpoint = endpoint
            subscription.p256dh_key = p256dh
            subscription.auth_key = auth
            subscription.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"Push subscription error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def install_prompt(request):
    """Show PWA installation prompt"""
    return render(request, 'pwa/install_prompt.html')


@login_required
def offline_page(request):
    """Offline page for PWA"""
    return render(request, 'pwa/offline.html')


def check_online_status(request):
    """Check if user is online"""
    return JsonResponse({
        'online': True,
        'timestamp': timezone.now().isoformat()
    })


@login_required
def sync_offline_data(request):
    """Sync offline data when back online"""
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            offline_actions = data.get('actions', [])
            
            results = []
            for action in offline_actions:
                try:
                    # Process offline action
                    result = process_offline_action(action, request.user)
                    results.append({
                        'id': action.get('id'),
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'id': action.get('id'),
                        'success': False,
                        'error': str(e)
                    })
            
            return JsonResponse({
                'success': True,
                'results': results
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def process_offline_action(action, user):
    """Process actions that were performed offline"""
    action_type = action.get('type')
    
    if action_type == 'complaint_create':
        from complaints.models import Complaint
        complaint = Complaint.objects.create(
            building_id=action['building_id'],
            apartment_id=action['apartment_id'],
            title=action['title'],
            description=action['description'],
            category=action.get('category', 'other'),
            created_by=user
        )
        return {'id': complaint.id, 'status': 'created'}
    
    elif action_type == 'notification_read':
        from notifications.models import Notification
        notification = Notification.objects.get(
            id=action['notification_id'],
            user=user
        )
        notification.mark_as_read()
        return {'status': 'marked_as_read'}
    
    # Add more action types as needed
    return {'status': 'unknown_action'}


@login_required
def app_shell(request):
    """App shell for PWA"""
    return render(request, 'pwa/app_shell.html', {
        'user': request.user,
        'notification_count': request.user.get_notification_count(),
        'complaint_count': request.user.get_complaint_count(),
    })
