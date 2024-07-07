from django.shortcuts import HttpResponse
from .models import Predictor
import os
import numpy as np
import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img
from io import BytesIO
from django.templatetags.static import static
import google.generativeai as genai
import markdown2
import requests



def populate_predictor_model(request):
    return HttpResponse("Predictor model populated successfully.")


def predict_disease(request, plant_id):
    print(f"Plant ID: {plant_id}")  # Print the plant ID to debug

    # Initialize S3 client
    s3 = boto3.client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                      region_name=settings.AWS_REGION_NAME)
    
    BUCKET_NAME = settings.AWS_S3_BUCKET_NAME

    if request.method == 'POST':
        print("POST request received.")  # Print when a POST request is received
        
        # Get the plant predictor model instance
        predictor = get_object_or_404(Predictor, id=plant_id)
        print(f"Predictor object retrieved: {predictor}")  # Print predictor object
        
        # Get the photo from the POST request
        photo = request.FILES.get('photo')
        print(f"Photo received: {photo}")  # Print the received photo

        if photo:
            try:
                # Upload the photo to S3
                print("Uploading photo to S3...")
                s3.upload_fileobj(photo, BUCKET_NAME, photo.name)
                photo_url = f'https://{BUCKET_NAME}.s3.amazonaws.com/{photo.name}'
                print(f"Photo URL after upload: {photo_url}")  # Print photo URL after upload
                
                # Preprocess the image
                img = preprocess_image(photo_url)

                # Load the model and labels
                print("Loading model and labels...")
                                # Generate the full path to the model file using STATIC_ROOT
                model_relative_path = predictor.model_path.lstrip('../static/').replace('\\', '/')
                labels_relative_path = predictor.labels_path.lstrip('../static/').replace('\\', '/')
                root_path = settings.ROOT.replace('\\', '/')
                model_full_path = os.path.join(root_path, model_relative_path)
                labels_full_path = os.path.join(root_path, labels_relative_path)
                model_full_path = model_full_path.replace('\\', '/')
                labels_full_path = labels_full_path.replace('\\', '/')
                model = load_model(model_full_path)
                labels = np.load(labels_full_path , allow_pickle=True)
                print("Model and labels loaded successfully.")  # Print success message
                
                # Predict the disease
                print("Predicting disease...")
                prediction = model.predict(img)
                predicted_label = labels[np.argmax(prediction)]
                print(f"Prediction: {predicted_label}")  # Print predicted label
                
                # Delete the image from S3 after prediction
                print("Deleting photo from S3...")
                s3.delete_object(Bucket=BUCKET_NAME, Key=photo.name)
                print("Photo deleted successfully.")  # Print success message
                genai.configure(settings.api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                crop=predictor.plant_name
                disease=predicted_label

                response = model.generate_content(f"Provide the solution and precautions for {disease} in {crop}.")
                html_content = markdown2.markdown(response.text)
                return render(request,'disease_predict.html',{'solution':html_content})
                # You can add more debugging here if needed

                # Render the response with solution text
            
            except NoCredentialsError:
                return render(request, 'disease_predict.html', {'error': 'AWS credentials not available.'})
            except Exception as e:
                print(f"Error occurred: {str(e)}")  # Print any errors that occur
                return render(request, 'disease_predict.html', {'error': str(e)})
        
        return render(request, 'disease_predict.html', {'error': 'No photo provided.'})

    return render(request, 'disease_predict.html', {'error': 'Invalid request method.'})

def preprocess_image(image_url):
    response = requests.get(image_url)
    img = load_img(BytesIO(response.content), target_size=(64, 64))  # Same target size as used in training
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0  # Rescale as done during training
    return img_array
