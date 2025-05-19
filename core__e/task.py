
import os
import random
import datetime
import cv2
from PIL import Image

from celery import shared_task
from django.conf import settings
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model

from roboflow import Roboflow
import supervision as sv

from .models import Analysis, Predictions, AnalysisResult

User = get_user_model()

@shared_task
def process_prediction(relative_image_path, user_id=None):
    """
    Processes an image using Roboflow, stores predictions and annotated results,
    and returns serializable output (file paths, analysis ID, and prediction labels).
    """
    try:
        full_image_path = os.path.join(settings.MEDIA_ROOT, relative_image_path)

        rf = Roboflow(api_key=settings.ROBO_API_KEY)
        model = rf.workspace().project("stage-1-launch").version(1).model

        prediction_data = model.predict(full_image_path, confidence=1).json()
        labels = [item["class"] for item in prediction_data.get("predictions", [])]
      
        user = User.objects.get(id=user_id) if user_id else None

        with transaction.atomic():
            analysis = Analysis.objects.create(raw_image=relative_image_path.replace("\\", "/"), user=user)

            prediction_objs = []
            for label in set(labels):
                obj, _ = Predictions.objects.get_or_create(result_prediction=label)
                prediction_objs.append(obj)
            analysis.predictions.set(prediction_objs)

            # Annotate image
            image = cv2.imread(full_image_path)
            detections = sv.Detections.from_roboflow(prediction_data)

            label_annotator = sv.LabelAnnotator()
            mask_annotator = sv.MaskAnnotator()
            annotated_image = mask_annotator.annotate(scene=image, detections=detections)
            annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)

            output_dir = os.path.join(settings.MEDIA_ROOT, "analyzed")
            os.makedirs(output_dir, exist_ok=True)

            filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}.jpeg"
            output_path = os.path.join(output_dir, filename)
            Image.fromarray(annotated_image).save(output_path, optimize=True, quality=85)

            analysis.analyzed_image = f"analyzed/{filename}"
            analysis.save()

        return (
            analysis.analyzed_image,
            analysis.raw_image,
            analysis.id,
            [obj.result_prediction for obj in prediction_objs],
        )

    except IntegrityError as e:
        print(f"[IntegrityError] {e}")
    except Exception as e:
        print(f"[Processing Error] {e}")

    return None, None, None, []
