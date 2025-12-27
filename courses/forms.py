from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Lesson, Topic


class LessonForm(forms.ModelForm):
    """Lesson form with CKEditor for description, notes, and questions fields"""
    description = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        required=False,
        label='Tavsif'
    )
    
    notes = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        required=False,
        label='Eslatmalar'
    )
    
    questions = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        required=False,
        label='Savollar'
    )
    
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'notes', 'questions', 'date', 'start_time', 'end_time', 'topic']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'topic': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Sarlavha',
            'description': 'Tavsif',
            'notes': 'Eslatmalar',
            'questions': 'Savollar',
            'date': 'Sana',
            'start_time': 'Boshlanish vaqti',
            'end_time': 'Tugash vaqti',
            'topic': 'Mavzu',
        }

