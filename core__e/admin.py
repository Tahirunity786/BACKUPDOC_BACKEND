from django.contrib import admin
from .models import Analysis, Predictions, AnalysisResult


# Register your models here.

admin.site.register(Analysis)
admin.site.register(Predictions)
admin.site.register(AnalysisResult)