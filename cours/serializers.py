from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (      
    Category, Course, CourseModule, Lesson, Assignment,
    Submission, Certificate, Comment, UserProfile, Notification,
    LessonCompletion
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']
        

class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'icon', 'order', 'created_at', 'course_count']
    
    def get_course_count(self, obj):
        return obj.course_set.count()

class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category_name = serializers.ReadOnlyField(source='category.name')
    student_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'price', 'is_featured', 'thumbnail', 'preview_video', 
            'requirements', 'what_you_learn', 'level', 'duration_hours', 
            'duration_minutes', 'category', 'category_name', 'instructor', 
            'enrollment_limit', 'is_active', 'created_at', 'updated_at', 
            'student_count', 'is_enrolled', 'progress'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'student_count', 'is_enrolled', 'progress']
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.students.filter(id=request.user.id).exists()
        return False
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            return None
            
        user = request.user
        
        # Obtenir le nombre total de leçons dans le cours
        lesson_count = Lesson.objects.filter(module__course=obj).count()
        if lesson_count == 0:
            return 0
            
        # Obtenir le nombre de leçons complétées par l'utilisateur
        completed_count = LessonCompletion.objects.filter(
            user=user,
            lesson__module__course=obj
        ).count()
        
        return round((completed_count / lesson_count) * 100, 1)
    

class CourseModuleSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = ['id', 'course', 'title', 'description', 'order', 'created_at', 'updated_at', 'lesson_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'lesson_count']
    
    def get_lesson_count(self, obj):
        return obj.lessons.count()

class LessonSerializer(serializers.ModelSerializer):
    module_title = serializers.ReadOnlyField(source='module.title')
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'module_title', 'title', 'content', 
            'video', 'order', 
            'created_at', 'updated_at', 'is_completed'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_completed']
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LessonCompletion.objects.filter(
                user=request.user,
                lesson=obj
            ).exists()
        return False

class LessonCompletionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.ReadOnlyField(source='lesson.title')
    
    class Meta:
        model = LessonCompletion
        fields = ['id', 'user', 'lesson', 'lesson_title', 'completed_at']
        read_only_fields = ['id', 'completed_at']

class AssignmentSerializer(serializers.ModelSerializer):
    lesson_title = serializers.ReadOnlyField(source='lesson.title')
    has_submitted = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'lesson', 'lesson_title', 'title', 'description', 
            'due_date', 'max_score', 'created_at', 
            'updated_at', 'has_submitted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'has_submitted']
    
    def get_has_submitted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Submission.objects.filter(
                assignment=obj,
                student=request.user
            ).exists()
        return False

class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    assignment_title = serializers.ReadOnlyField(source='assignment.title')
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 
            'student_name', 'file', 'file_url', 'submitted_at', 
            'score', 'feedback', 'graded_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'graded_at', 'student_name', 'assignment_title', 'file_url']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}" if obj.student.first_name else obj.student.username
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_file(self, value):
        # Vérifier la taille du fichier (10 Mo max)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
        
        # Vérifier l'extension du fichier
        allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.zip', '.py', '.java', '.js', '.html', '.css']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"L'extension du fichier n'est pas autorisée. Extensions autorisées: {', '.join(allowed_extensions)}")
        
        return value

class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    course_title = serializers.ReadOnlyField(source='course.title')
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'user', 'user_name', 'course', 'course_title', 
            'certificate_number', 'issued_date', 'pdf_file'
        ]
        read_only_fields = ['id', 'certificate_number', 'issue_date', 'user_name', 'course_title']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'lesson', 'parent', 
             'content', 'created_at', 
           
        ]
        read_only_fields = ['id', 'created_at', 'user', 'parent']
    
    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.user
    
    def get_parent(self, obj):
        if obj.parent:
            return obj.parent.content[:50] + '...' if len(obj.parent.content) > 50 else obj.parent.content
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'avatar',  
            'social_links',  'skills', 
             'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        return super().update(instance, validated_data)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type', 
            'read', 'created_at', 'link'
        ]
        read_only_fields = ['id', 'created_at']


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.username')
    assignment_title = serializers.ReadOnlyField(source='assignment.title')
    submitted_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_name',
            'submitted_at', 'submitted_at_formatted', 'file', 'grade', 'feedback',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']
    
    def get_submitted_at_formatted(self, obj):
        return obj.submitted_at.strftime('%d %b %Y, %H:%M')