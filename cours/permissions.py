from rest_framework import permissions
from .models import Course, CourseModule, Lesson, Assignment

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission permettant uniquement aux administrateurs de modifier le contenu.
    Les utilisateurs non authentifiés peuvent uniquement accéder en lecture.
    """
    
    def has_permission(self, request, view):
        # Autorise les demandes en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Exige que l'utilisateur soit authentifié et administrateur pour les autres méthodes
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission permettant uniquement aux instructeurs de modifier leurs propres cours.
    Les utilisateurs non authentifiés peuvent uniquement accéder en lecture.
    """
    
    def has_permission(self, request, view):
        # Autorise les demandes en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Exige que l'utilisateur soit authentifié pour les autres méthodes
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Autorise les demandes en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Autorise les modifications uniquement par l'instructeur du cours
        return obj.instructor == request.user or request.user.is_staff

class IsEnrolledInCourse(permissions.BasePermission):
    """
    Permission permettant aux utilisateurs inscrits à un cours d'accéder à son contenu.
    Les instructeurs ont également accès.
    """
    
    def has_permission(self, request, view):
        # Exige que l'utilisateur soit authentifié
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Les administrateurs ont toujours accès
        if request.user.is_staff:
            return True
            
        # Pour les actions sur la liste, autoriser l'accès
        if view.action in ['list', 'create']:
            return True
            
        return True  # La vérification détaillée se fait dans has_object_permission
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_staff:
            return True
            
        # Déterminer le cours associé selon le type d'objet
        course = None
        
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module') and hasattr(obj.module, 'course'):
            course = obj.module.course
        elif hasattr(obj, 'lesson') and hasattr(obj.lesson, 'module') and hasattr(obj.lesson.module, 'course'):
            course = obj.lesson.module.course
        
        if not course:
            return False
            
        # Autoriser l'accès si l'utilisateur est l'instructeur du cours
        if course.instructor == request.user:
            return True
            
        # Autoriser l'accès si l'utilisateur est inscrit au cours
        return course.students.filter(id=request.user.id).exists()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission permettant uniquement aux propriétaires d'un objet de le modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        # Autorise les demandes en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Autorise les modifications uniquement par le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'student'):
            return obj.student == request.user
        
        return False

class IsCourseInstructor(permissions.BasePermission):
    """
    Permission permettant uniquement aux instructeurs d'un cours de modifier ses modules et leçons.
    """
    
    def has_permission(self, request, view):
        # Exige que l'utilisateur soit authentifié
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Les administrateurs ont toujours accès
        if request.user.is_staff:
            return True
            
        # Pour les actions de création, vérifier si l'utilisateur est l'instructeur du cours
        if view.action == 'create':
            course_id = request.data.get('course_id')
            if not course_id:
                return False
                
            try:
                course = Course.objects.get(id=course_id)
                return course.instructor == request.user
            except Course.DoesNotExist:
                return False
                
        return True  # La vérification détaillée se fait dans has_object_permission
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_staff:
            return True
            
        # Déterminer le cours associé selon le type d'objet
        course = None
        
        if isinstance(obj, Course):
            course = obj
        elif isinstance(obj, CourseModule):
            course = obj.course
        elif isinstance(obj, Lesson):
            course = obj.module.course
        elif isinstance(obj, Assignment):
            course = obj.lesson.module.course
            
        if not course:
            return False
            
        # Autoriser les modifications uniquement par l'instructeur du cours
        return course.instructor == request.user