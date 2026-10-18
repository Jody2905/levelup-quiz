from django.contrib import admin

from .models import Attempt, AttemptAnswer, Category, Choice, Level, Question, Quiz


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "description"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "level", "category", "time_limit_minutes", "is_published"]
    list_filter = ["level", "category", "is_published"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [QuestionInline]

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "quiz", "order"]
    list_filter = ["quiz__level", "quiz"]
    search_fields = ["text"]
    inlines = [ChoiceInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ["question", "selected_choice", "is_correct"]
    can_delete = False


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "quiz", "score", "total", "started_at", "submitted_at", "timed_out"]
    list_filter = ["quiz__level", "quiz", "timed_out"]
    readonly_fields = ["user", "quiz", "started_at", "submitted_at", "question_order", "score", "total", "timed_out"]
    inlines = [AttemptAnswerInline]
