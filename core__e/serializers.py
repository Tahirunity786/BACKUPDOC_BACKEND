# serializers.py
from rest_framework import serializers
from .models import Analysis, Predictions

class PredictionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predictions
        fields = '__all__'

class AnalysisSerializer(serializers.ModelSerializer):
    predictions = PredictionsSerializer(many=True)

    class Meta:
        model = Analysis
        fields = [
            'id', 'raw_image', 'analyzed_image', 'predictions',
            'note', 'report_analysis', 'date_time', 'is_corrected'
        ]
