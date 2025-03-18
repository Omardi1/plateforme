
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import SubmissionViewSet

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'modules', views.CourseModuleViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'assignments', views.AssignmentViewSet)
router.register(r'certificates', views.CertificateViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'submissions', SubmissionViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]