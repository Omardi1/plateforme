from django.contrib import admin

# Register your models here.


from .models import (
    Category, Course, CourseModule, Assignment, Submission,
    Certificate, Comment, UserProfile, Notification
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'price', 'is_featured', 'level')
    list_filter = ('category', 'is_featured', 'level')
    search_fields = ('id', 'category__name', 'price')
    ordering = ('category', 'price')

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    ordering = ('course', 'order')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'due_date', 'points')
    list_filter = ('due_date',)
    search_fields = ('title',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'grade')
    list_filter = ('assignment',)
    search_fields = ('student__username', 'assignment__title')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'issued_date', 'certificate_number')
    search_fields = ('user__username', 'certificate_number')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'created_at')
    search_fields = ('user__username', 'lesson__title')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__username',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read')
    search_fields = ('title',)

