from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    # PWA: manifest and service worker must be served from the root scope so the
    # SW can intercept '/' navigations (browsers restrict SW scope to its origin path).
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="manifest",
    ),
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="sw.js",
            content_type="application/javascript",
        ),
        name="service_worker",
    ),
    path('', include('apps.sessions.urls')),
    path('', include('apps.polls.urls')),
    path('', include('apps.matches.urls')),
    path('', include('apps.payments.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.donations.urls')),
    path('', include('apps.banking.urls')),
    path('gdpr/', include('apps.gdpr.urls')),
    path("accounts/", include("allauth.urls")),
]

# Serve user-uploaded media from the dev server only. In staging/prod media is
# served by Cloudinary (CLOUDINARY_URL) so this route is intentionally not added.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
