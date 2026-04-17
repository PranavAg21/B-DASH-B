from django.urls import path
from .views import dataset_list, dataset_data, delete_dataset, ai_insights

urlpatterns = [
    path('datasets/', dataset_list),
    path('datasets/<int:id>/', dataset_data),
    path('datasets/delete/<int:id>/', delete_dataset),
    path('datasets/ai-insights/', ai_insights),
]