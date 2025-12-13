from django.contrib import admin
from .models import Exam, Question, Answer, ExamResult, StudentAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'group', 'exam_type', 'date', 'max_score', 'passing_score', 'is_active']
    list_filter = ['exam_type', 'course', 'is_active', 'date', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-date']
    date_hierarchy = 'date'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'exam', 'question_type', 'points', 'order']
    list_filter = ['exam', 'question_type', 'created_at']
    search_fields = ['question_text']
    ordering = ['exam', 'order']
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['answer_text', 'question', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__exam']
    search_fields = ['answer_text']
    ordering = ['question', 'order']


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'percentage', 'is_passed', 'submitted_at']
    list_filter = ['exam', 'is_passed', 'submitted_at', 'created_at']
    search_fields = ['student__username', 'student__email', 'exam__title']
    ordering = ['-score', '-submitted_at']
    readonly_fields = ['score', 'percentage', 'is_passed']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['exam_result', 'question', 'created_at']
    list_filter = ['exam_result__exam', 'created_at']
    search_fields = ['exam_result__student__username', 'question__question_text']
    ordering = ['-created_at']
    filter_horizontal = ['selected_answers']
