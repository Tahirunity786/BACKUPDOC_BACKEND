from django.urls import path
from core__e.views import *

urlpatterns = [
    path('annotate/', EngineView.as_view(), name="annotate"),
    path('analysis/<int:analysis_id>/', AnalysisUpdateDeleteView.as_view(), name='update-delete-analysis'),
    path('result/<str:task_id>/', TaskResultView.as_view(), name="result"),
    path('analysis-list/', UserAnalysisListView.as_view(), name='user-analyses'),
    path('analyses/filter/', FilteredAnalysisListView.as_view(), name='user-analyses-filter'),
    path('analysis/email/<int:analysis_id>/', EmailAnalysisView.as_view(), name='user-analyses-email'),
]