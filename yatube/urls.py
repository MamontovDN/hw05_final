from django.contrib.flatpages import views as flat_v
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404, handler500  # noqa
from django.conf import settings
from django.conf.urls.static import static

handler404 = "posts.views.page_not_found"  # noqa
handler500 = "posts.views.server_error"  # noqa


urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', include('django.contrib.flatpages.urls')),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls')),
]
urlpatterns += [
    path('about-us/', flat_v.flatpage, {'url': '/about-us/'}, name='about'),
    path('terms/', flat_v.flatpage, {'url': '/terms/'}, name='terms'),
    path('about-author/', flat_v.flatpage,
         {'url': '/about-author/'}, name='author'),
    path('about-spec/', flat_v.flatpage, {'url': '/about-spec/'}, name='spec'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ]