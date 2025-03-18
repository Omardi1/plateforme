from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='categories/')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_featured = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='courses/')
    preview_video = models.URLField(blank=True)
    requirements = models.JSONField(default=list)
    what_you_learn = models.JSONField(default=list)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ])
    duration_hours = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)
    enrollment_limit = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CourseModule(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

class Lesson(models.Model):
    module = models.ForeignKey(CourseModule, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    video = models.FileField(upload_to='lessons/videos/', null=True, blank=True)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

class Assignment(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='assignments', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100) 
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='submissions/')
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_date = models.DateTimeField(auto_now_add=True)
    certificate_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='certificates/')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked')
    ], default='pending')

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    social_links = models.URLField(blank=True) 
    skills = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=[
        ('assignment', 'New Assignment'),
        ('grade', 'New Grade'),
        ('comment', 'New Comment'),
        ('certificate', 'New Certificate'),
    ])
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LessonCompletion(models.Model):
    """
    Modèle pour suivre les leçons complétées par chaque utilisateur.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_lessons')
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-completed_at']
        verbose_name = 'Leçon complétée'
        verbose_name_plural = 'Leçons complétées'
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"