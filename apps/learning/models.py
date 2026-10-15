from django.db import models
from django.conf import settings


class StudyPlan(models.Model):
    """AI-generated learning plan for a specific skill."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_plans'
    )
    skill_name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    target_level = models.CharField(max_length=50, blank=True, default='')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    estimated_hours = models.IntegerField(default=0)
    progress_percent = models.IntegerField(default=0)
    ai_summary = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Study Plan'
        verbose_name_plural = 'Study Plans'

    def __str__(self):
        return f"{self.user.email} - {self.skill_name}"

    def update_progress(self):
        total = self.lessons.count()
        if total == 0:
            self.progress_percent = 0
        else:
            done = self.lessons.filter(is_completed=True).count()
            self.progress_percent = int((done / total) * 100)
        if self.progress_percent == 100:
            self.status = 'completed'
        elif self.status == 'completed':
            self.status = 'active'
        self.save(update_fields=['progress_percent', 'status', 'updated_at'])


class StudyPlanLesson(models.Model):
    """A single lesson within a study plan."""

    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    order = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=300)
    content = models.TextField(blank=True, default='')
    key_points = models.JSONField(default=list, blank=True)
    resources = models.JSONField(default=list, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['plan', 'order']
        unique_together = ['plan', 'order']
        verbose_name = 'Study Plan Lesson'
        verbose_name_plural = 'Study Plan Lessons'

    def __str__(self):
        return f"{self.plan.skill_name}: {self.title}"


class Quiz(models.Model):
    """A quiz attached to a study plan to test understanding."""

    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    title = models.CharField(max_length=300)
    questions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return f"{self.plan.skill_name}: {self.title}"

    @property
    def total_questions(self):
        return len(self.questions)


class QuizAttempt(models.Model):
    """A user's attempt at a quiz."""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    answers = models.JSONField(default=list, blank=True)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'

    def __str__(self):
        return f"{self.user.email}: {self.quiz.title} {self.percentage:.0f}%"


class LearningGoal(models.Model):
    """A user's weekly learning goal with automatic progress tracking."""

    GOAL_TYPE_CHOICES = [
        ('lessons', 'Complete Lessons'),
        ('quizzes', 'Complete Quizzes'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_goal'
    )
    goal_type = models.CharField(max_length=10, choices=GOAL_TYPE_CHOICES, default='lessons')
    target = models.PositiveIntegerField(default=5)
    period_start = models.DateField(auto_now_add=True)
    achieved = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    achievement_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Learning Goal'
        verbose_name_plural = 'Learning Goals'

    def __str__(self):
        return f"{self.user.email}: {self.goal_type} {self.achieved}/{self.target}"

    def progress_percent(self):
        if self.target <= 0:
            return 0
        return min(int((self.achieved / self.target) * 100), 100)

    def is_complete(self):
        return self.achieved >= self.target

    def refresh_progress(self):
        """Recompute achieved progress from DB and roll a new week if past period."""
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.localdate()
        # Roll to a new week if the period has ended
        while self.period_start <= today - timedelta(days=7):
            self.period_start += timedelta(days=7)
            self.achieved = 0

        if self.goal_type == 'lessons':
            count = StudyPlanLesson.objects.filter(
                plan__user=self.user,
                is_completed=True,
                completed_at__date__gte=self.period_start,
                completed_at__date__lte=today,
                completed_at__isnull=False,
            ).count()
        else:
            count = QuizAttempt.objects.filter(
                user=self.user,
                passed=True,
                created_at__date__gte=self.period_start,
                created_at__date__lte=today,
            ).count()

        self.achieved = count
        was_achieved = self.is_complete()
        self.save(update_fields=['achieved', 'period_start', 'updated_at'])

        # Send a one-time notification when the goal becomes complete
        if was_achieved and not self.achievement_notified:
            self._notify_goal_achieved()
        # Reset the notification flag on a new week / when no longer complete
        elif not was_achieved and self.achievement_notified:
            self.achievement_notified = False
            self.save(update_fields=['achievement_notified', 'updated_at'])

        return self

    def _notify_goal_achieved(self):
        """Create an in-app notification congratulating the user."""
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=self.user,
                title='Weekly Goal Achieved! 🎉',
                message=(
                    f'Congratulations! You completed your weekly goal of {self.target} '
                    f'{self.get_goal_type_display().lower()} — keep up the great momentum!'
                ),
                notification_type='system',
                link='/learning/',
            )
            self.achievement_notified = True
            self.save(update_fields=['achievement_notified', 'updated_at'])
        except Exception:
            pass
