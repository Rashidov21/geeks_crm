from django import forms
from django.utils import timezone
from ckeditor.widgets import CKEditorWidget
from .models import Homework, HomeworkGrade


class HomeworkForm(forms.ModelForm):
    """Homework form with CKEditor for assignment_description field"""
    assignment_description = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        required=False,
        label='Vazifa tavsifi'
    )
    
    class Meta:
        model = Homework
        fields = ['lesson', 'title', 'assignment_description', 'file', 'link', 'code', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'code': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
        }
        labels = {
            'lesson': 'Dars',
            'title': 'Sarlavha',
            'assignment_description': 'Vazifa tavsifi',
            'file': 'Fayl',
            'link': 'Link',
            'code': 'Kod',
            'deadline': 'Muddati',
        }
    
    def clean_deadline(self):
        """Deadline validatsiyasi"""
        deadline = self.cleaned_data['deadline']
        if deadline and deadline < timezone.now():
            raise forms.ValidationError("Deadline o'tmish bo'lishi mumkin emas")
        return deadline
    
    def clean_file(self):
        """File upload validatsiyasi"""
        file = self.cleaned_data.get('file')
        if file:
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError("Fayl hajmi 10MB dan oshmasligi kerak")
        return file


class HomeworkGradeForm(forms.ModelForm):
    """Homework grade form with CKEditor for comment field"""
    comment = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        required=False,
        label='Izoh'
    )
    
    class Meta:
        model = HomeworkGrade
        fields = ['grade', 'comment']
        widgets = {
            'grade': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'class': 'form-control',
                'step': 1
            }),
        }
        labels = {
            'grade': 'Baho (0-100)',
            'comment': 'Izoh',
        }
    
    def clean_grade(self):
        """Grade validatsiyasi"""
        grade = self.cleaned_data['grade']
        if grade < 0 or grade > 100:
            raise forms.ValidationError("Baho 0 dan 100 gacha bo'lishi kerak")
        return grade

