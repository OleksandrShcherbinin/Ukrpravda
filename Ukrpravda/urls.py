from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from News import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('news/<slug:slug>', views.ArticleView.as_view(), name='single'),
    path('article/', views.ArticlesView.as_view(), name='article'),
    path('article/<slug:slug>', views.DetailArticleView.as_view(), name='s_article'),
    path('columns/', views.ColumnsView.as_view(), name='columns'),
    path('columns/<slug:slug>', views.DetailColumnView.as_view(), name='s_column'),
    path('', views.SearchView.as_view(), name='search'),

    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    #path('robots.txt', views.robots_view)

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

