import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Predictions(models.Model):
    result_prediction = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.result_prediction

class Analysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='analyses')  # assuming doctor is a user
    raw_image = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    analyzed_image = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    predictions = models.ManyToManyField(Predictions, related_name="analyses")
    note = models.TextField(null=True, blank=True)
    report_analysis = models.TextField(null=True, blank=True)
    date_time = models.DateTimeField(auto_now_add=True)
    is_corrected = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='NA'
    )

    def __str__(self):
        return f"Analysis #{self.id}"


class AnalysisResult(models.Model):
    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    analysis = models.ManyToManyField(Analysis, blank=True, related_name='analysis_results')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        analyses = self.analysis.all()
        if analyses.exists():
            return f"Result for Analysis #{analyses.first().id}"
        return f"Result ID: {self.analysis_id}"
