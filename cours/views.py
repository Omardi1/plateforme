from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Comment
from .serializers import CommentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q
from django.core.paginator import Paginator
import logging
from .models import UserProfile
from .serializers import UserProfileSerializer
import time
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Submission
from .serializers import SubmissionSerializer
from .models import (
    Category, Course, CourseModule, Lesson, Assignment,
    Submission, Certificate, Comment, UserProfile, Notification,
    LessonCompletion  # Nouveau modèle ajouté
)
from .serializers import (
    CategorySerializer, CourseSerializer, CourseModuleSerializer, LessonSerializer,
    AssignmentSerializer, SubmissionSerializer, CertificateSerializer, CommentSerializer,
    UserProfileSerializer, NotificationSerializer, LessonCompletionSerializer  # Nouveau serializer
)
from .permissions import (
    IsInstructorOrReadOnly, IsEnrolledInCourse, IsOwnerOrReadOnly, 
    IsCourseInstructor, IsAdminOrReadOnly
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

# Configuration du logger
logger = logging.getLogger(__name__)



class LessonViewSet(viewsets.ModelViewSet):
    # Seuls les utilisateurs authentifiés peuvent voir les leçons
    permission_classes = [IsAuthenticated]
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        # Permet la lecture publique, mais nécessite l'authentification pour les modifications
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


        
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')  # Trie les commentaires par date décroissante
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

# ---------------------------
# Vues pour la gestion des catégories
# ---------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]  # Seuls les admins peuvent modifier
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def perform_create(self, serializer):
        serializer.save()
        logger.info(f"Catégorie créée: {serializer.data.get('name')} par {self.request.user}")

# ---------------------------
# Vues pour la gestion des cours
# ---------------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrReadOnly]  # Permission personnalisée
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'instructor__username']
    ordering_fields = ['title', 'created_at', 'start_date']

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
        logger.info(f"Cours créé: {serializer.data.get('title')} par {self.request.user}")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """
        Permet à un utilisateur authentifié de s'inscrire à un cours.
        Vérifie la limite d'inscription si définie et les prérequis.
        """
        course = self.get_object()
        user = request.user

        # Vérifier si l'utilisateur est déjà inscrit
        if course.students.filter(id=user.id).exists():
            return Response({"detail": "Vous êtes déjà inscrit à ce cours."},
                            status=status.HTTP_400_BAD_REQUEST)
                            
        # Vérifier la limite d'inscription
        if course.enrollment_limit and course.students.count() >= course.enrollment_limit:
            return Response({"detail": "La limite d'inscription a été atteinte."},
                            status=status.HTTP_400_BAD_REQUEST)
                            
        # Vérifier les prérequis (si implémentés)
        prerequisites = course.prerequisites.all()
        if prerequisites:
            completed_prereqs = Certificate.objects.filter(
                user=user, 
                course__in=prerequisites
            ).count()
            
            if completed_prereqs < prerequisites.count():
                return Response(
                    {"detail": "Vous devez compléter tous les prérequis avant de vous inscrire."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        try:
            course.students.add(user)
            course.save()
            
            # Créer une notification pour l'utilisateur
            Notification.objects.create(
                user=user,
                title=f"Inscription réussie",
                message=f"Vous êtes maintenant inscrit au cours: {course.title}",
                notification_type="enrollment"
            )
            
            logger.info(f"Utilisateur {user.username} inscrit au cours {course.title}")
            return Response({"detail": "Inscription réussie."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {str(e)}")
            return Response(
                {"detail": "Une erreur est survenue lors de l'inscription."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unenroll(self, request, pk=None):
        """
        Permet à un utilisateur de se désinscrire d'un cours.
        """
        course = self.get_object()
        user = request.user
        
        if not course.students.filter(id=user.id).exists():
            return Response({"detail": "Vous n'êtes pas inscrit à ce cours."},
                            status=status.HTTP_400_BAD_REQUEST)
                            
        try:
            course.students.remove(user)
            course.save()
            
            logger.info(f"Utilisateur {user.username} désinscrit du cours {course.title}")
            return Response({"detail": "Désinscription réussie."}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la désinscription: {str(e)}")
            return Response(
                {"detail": "Une erreur est survenue lors de la désinscription."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """
        Liste paginée des cours dans lesquels l'utilisateur authentifié est inscrit.
        """
        user = request.user
        
        # Filtrer par statut si demandé
        status_filter = request.query_params.get('status', None)
        
        courses = Course.objects.filter(students=user)
        if status_filter:
            if status_filter == 'active':
                courses = courses.filter(is_active=True)
            elif status_filter == 'completed':
                # Logique pour déterminer les cours complétés
                # (par exemple, tous les modules sont marqués comme complétés)
                pass
                
        # Pagination
        page_size = int(request.query_params.get('page_size', 10))
        page_number = int(request.query_params.get('page', 1))
        
        paginator = Paginator(courses, page_size)
        paginated_courses = paginator.get_page(page_number)
        
        serializer = self.get_serializer(paginated_courses, many=True)
        
        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_number,
            'results': serializer.data
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsEnrolledInCourse])
    def content(self, request, pk=None):
        """
        Retourne le contenu complet d'un cours (modules et leçons) pour une consultation détaillée.
        L'utilisateur doit être inscrit au cours pour y accéder.
        """
        course = self.get_object()
        user = request.user
        
        # Vérifier si l'utilisateur est l'instructeur ou un étudiant inscrit
        if not (course.instructor == user or course.students.filter(id=user.id).exists()):
            return Response(
                {"detail": "Vous devez être inscrit à ce cours pour accéder à son contenu."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            modules = course.modules.all().order_by('order')
            module_data = []
            
            for module in modules:
                lessons = module.lessons.all().order_by('order')
                module_serializer = CourseModuleSerializer(module)
                lessons_serializer = LessonSerializer(lessons, many=True)
                
                # Pour chaque leçon, vérifier si elle est complétée par l'utilisateur
                lesson_data = lessons_serializer.data
                for lesson in lesson_data:
                    lesson['completed'] = LessonCompletion.objects.filter(
                        user=user,
                        lesson_id=lesson['id']
                    ).exists()
                
                module_data.append({
                    "module": module_serializer.data,
                    "lessons": lesson_data
                })
                
            return Response(module_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contenu: {str(e)}")
            return Response(
                {"detail": "Une erreur est survenue lors de la récupération du contenu du cours."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ---------------------------
# Vues pour la gestion des modules de cours
# ---------------------------
class CourseModuleViewSet(viewsets.ModelViewSet):
    queryset = CourseModule.objects.all()
    serializer_class = CourseModuleSerializer
    permission_classes = [IsAuthenticated, IsCourseInstructor]  # Permission personnalisée
    
    def get_queryset(self):
        # Filtrer par cours si spécifié
        course_id = self.request.query_params.get('course_id', None)
        if course_id:
            return CourseModule.objects.filter(course_id=course_id).order_by('order')
        return CourseModule.objects.all()
        
    def perform_create(self, serializer):
        # Vérifier que l'utilisateur est bien l'instructeur du cours
        course_id = self.request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        if course.instructor != self.request.user:
            raise ValidationError("Vous n'êtes pas autorisé à ajouter des modules à ce cours.")
            
        serializer.save()
        logger.info(f"Module créé pour le cours {course_id} par {self.request.user}")

# ---------------------------
# Vues pour la gestion des leçons
# ---------------------------
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse]  # Permission personnalisée

    def get_queryset(self):
        # Filtrer par module si spécifié
        module_id = self.request.query_params.get('module_id', None)
        if module_id:
            return Lesson.objects.filter(module_id=module_id).order_by('order')
        return Lesson.objects.all()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_completed(self, request, pk=None):
        """
        Marque une leçon comme complétée par l'utilisateur.
        Utilise le modèle LessonCompletion pour stocker cette information.
        """
        lesson = self.get_object()
        user = request.user
        
        # Vérifier que l'utilisateur est inscrit au cours
        course = lesson.module.course
        if not course.students.filter(id=user.id).exists():
            return Response(
                {"detail": "Vous devez être inscrit à ce cours pour marquer des leçons comme terminées."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            completion, created = LessonCompletion.objects.get_or_create(
                user=user,
                lesson=lesson,
                defaults={"completed_at": timezone.now()}
            )
            
            if not created:
                # Mettre à jour la date de completion si déjà existante
                completion.completed_at = timezone.now()
                completion.save()
                
            # Vérifier si toutes les leçons du module sont terminées
            module = lesson.module
            total_lessons = module.lessons.count()
            completed_lessons = LessonCompletion.objects.filter(
                user=user,
                lesson__module=module
            ).count()
            
            # Si toutes les leçons sont terminées, notifier l'utilisateur
            if total_lessons == completed_lessons:
                Notification.objects.create(
                    user=user,
                    title=f"Module terminé",
                    message=f"Vous avez terminé le module '{module.title}' du cours '{course.title}'",
                    notification_type="progression"
                )
                
            # Vérifier si tous les modules du cours sont terminés
            total_modules = course.modules.count()
            completed_modules = 0
            
            for course_module in course.modules.all():
                module_lessons = course_module.lessons.count()
                if module_lessons == 0:  # Module sans leçons
                    continue
                    
                completed_module_lessons = LessonCompletion.objects.filter(
                    user=user,
                    lesson__module=course_module
                ).count()
                
                if module_lessons == completed_module_lessons:
                    completed_modules += 1
                    
            # Si tous les modules sont terminés, générer un certificat
            if total_modules > 0 and completed_modules == total_modules:
                certificate, cert_created = Certificate.objects.get_or_create(
                    user=user,
                    course=course,
                    defaults={"certificate_number": f"CERT-{user.id}-{course.id}-{int(time.time())}"}
                )
                
                Notification.objects.create(
                    user=user,
                    title=f"Cours terminé",
                    message=f"Félicitations ! Vous avez terminé le cours '{course.title}'. Un certificat a été généré.",
                    notification_type="achievement"
                )
                
            return Response(
                {"detail": f"La leçon '{lesson.title}' a été marquée comme terminée."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la leçon: {str(e)}")
            return Response(
                {"detail": "Une erreur est survenue lors du marquage de la leçon."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ---------------------------
# Vues pour la gestion des devoirs/assignments
# ---------------------------
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsEnrolledInCourse]  # Permission personnalisée

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """
        Permet à un étudiant de soumettre son devoir.
        Valide le type de fichier et sa taille avant soumission.
        """
        assignment = self.get_object()
        user = request.user


# ---------------------------
# Vues pour la gestion des certificats
# ---------------------------
class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrer pour que l'utilisateur ne voie que ses propres certificats
        if self.request.user.is_staff:
            return Certificate.objects.all()
        return Certificate.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def generate(self, request):
        """
        Génère un certificat pour l'utilisateur pour un cours terminé.
        On attend un 'course_id' dans le payload.
        """
        user = request.user
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({"detail": "course_id est requis."},
                            status=status.HTTP_400_BAD_REQUEST)
        course = get_object_or_404(Course, id=course_id)
        
        # Vérifier si l'utilisateur a complété le cours
        modules = course.modules.all()
        all_completed = True
        
        for module in modules:
            lessons = module.lessons.all()
            for lesson in lessons:
                if not LessonCompletion.objects.filter(user=user, lesson=lesson).exists():
                    all_completed = False
                    break
            if not all_completed:
                break
                
        if not all_completed:
            return Response(
                {"detail": "Vous devez compléter toutes les leçons du cours pour obtenir un certificat."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        certificate, created = Certificate.objects.get_or_create(
            user=user,
            course=course,
            defaults={"certificate_number": f"CERT-{user.id}-{course.id}-{int(time.time())}"}
        )
        
        serializer = CertificateSerializer(certificate)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['GET'])
    def my_profile(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment', 'student', 'grade']
    search_fields = ['assignment__title', 'student__username', 'feedback']
    ordering_fields = ['submitted_at', 'grade', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if not user.is_staff and not user.is_superuser:
            if hasattr(user, 'instructor_profile'):
                # Instructors can see submissions for their assignments
                queryset = queryset.filter(assignment__course__instructor=user)
            else:
                # Students can only see their own submissions
                queryset = queryset.filter(student=user)
                
        return queryset
    
    def perform_create(self, serializer):
        # Set the student to the current user if not provided
        if not self.request.data.get('student'):
            serializer.save(student=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def grade_submission(self, request, pk=None):
        submission = self.get_object()
        
        # Check permissions (only instructors can grade)
        if not request.user.is_staff and not hasattr(request.user, 'instructor_profile'):
            return Response({"detail": "You do not have permission to grade submissions."}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # Update grade and feedback
        grade = request.data.get('grade')
        feedback = request.data.get('feedback', '')
        
        if grade is None:
            return Response({"detail": "Grade is required."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        submission.grade = grade
        submission.feedback = feedback
        submission.save()
        
        return Response(SubmissionSerializer(submission).data)
    
    @action(detail=False, methods=['get'])
    def my_submissions(self, request):
        """Get all submissions for the current user"""
        queryset = self.get_queryset().filter(student=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_grading(self, request):
        """Get all submissions pending grading (for instructors)"""
        if not request.user.is_staff and not hasattr(request.user, 'instructor_profile'):
            return Response({"detail": "You do not have permission to access pending submissions."}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.get_queryset().filter(grade__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)