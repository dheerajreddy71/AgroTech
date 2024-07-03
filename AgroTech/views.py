# views.py

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
import requests
import joblib
import numpy as np
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import markdown2

def home(request):
    if request.method == 'POST':
        # Assuming form fields are named 'nitrogen', 'phosphorus', 'potassium'
        nitrogen = request.POST.get('nitrogen')
        phosphorus = request.POST.get('phosphorus')
        potassium = request.POST.get('potassium')
        
        # You can process the received data here, save to database, etc.
        # Example:
        # Save to database or perform any required operations
        
        # Pass data to template
        context = {
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': potassium,
        }
        return HttpResponseRedirect("../crop-recomm/",context)
    else:
        # Handle if not a POST request
        return render(request, 'index.html', {})


def predict_crop(request):
    if(request.method=='POST'):
        # WeatherAPI.com API endpoint
        url = "http://api.weatherapi.com/v1/current.json"
        # Replace with your API key
        api_key = "92d97ca8dbc849c1bd292506242806"
        # Replace with the location you want to get weather for
        location=''
        ip=0
        try:
            response = requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()  # Raise an exception for HTTP errors
            ip_data = response.json()
            ip = ip_data.get('ip')
        except Exception as e:
            print(e)

        try:
            response = requests.get(f"https://ipinfo.io/{ip}?token=d0b1e730faff23")
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            location= data.get('city')
        except requests.RequestException as e:
            print(e)
            

        # location = request.POST.get("city")
        # Construct the full API request URL with API key and location
        params = {
            "key": api_key,
            "q": location,
            "aqi": "no"  # Set to "yes" to include air quality data
        }
        

        # Make the API request
        response = requests.get(url, params=params)
        temperature=condition=humidity=wind_speed=''

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Extract relevant weather information
            location_name = data["location"]["name"]
            temperature = data["current"]["temp_c"]
            condition = data["current"]["condition"]["text"]
            humidity = data["current"]["humidity"]
            wind_speed = data["current"]["wind_kph"]

            # Print the weather information
            print(f"Current weather in {location_name}:")
            print(f"Temperature: {temperature}°C")
            print(f"Condition: {condition}")
            print(f"Humidity: {humidity}%")
            print(f"Wind speed: {wind_speed} km/h")
        else:
            print("Failed to retrieve weather data.")

        # temperature=20.879744
        # humidity=82.002744	

        N = int(request.POST.get('nitrogen'))
        P = int(request.POST.get('phosphorus'))
        K = int(request.POST.get('potassium'))
        ph =float(request.POST.get('ph'))
        rainfall =float(request.POST.get('rainfall'))
        # state = request.form.get("stt")
        crop_recommendation_model = crop_recommendation_model = joblib.load('D:/Hackathons/Persunethon/AgriDoctor/static/RandomForest.pkl')
        
        data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        my_prediction = crop_recommendation_model.predict(data)
        final_prediction = my_prediction[0]
        print(final_prediction)

        dict={'temperature':temperature,'humidity':humidity,'recomm':final_prediction,'location':location}
        return render(request, 'crop_predict.html', dict)
    return render(request, 'crop_predict.html')

def care_advisor(request):
    if request.method=='POST':
        crop=request.POST.get('planted_crop')
        city=''
        ip=0
        try:
            response = requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()  # Raise an exception for HTTP errors
            ip_data = response.json()
            ip = ip_data.get('ip')
        except Exception as e:
            print(e)

        try:
            response = requests.get(f"https://ipinfo.io/{ip}?token=d0b1e730faff23")
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            city= data.get('city')
        except requests.RequestException as e:
            print(e)
            

        genai.configure(api_key="AIzaSyCjwZlJg2vyF0_uC6ZI2XDGTYy5wmNScW4")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(f'''Generate a detailed environmental suitability report for the optimal growth of {crop}, including a comparison of current conditions with ideal conditions and recommendations for improvement if needed. Use the following format:
        Crop Information:
        Name of the crop: Sugarcane
        Current Environmental Conditions(get the current environmental conditions as if it is in {city}):
        Soil type: [Enter soil type]
        pH level: [Enter pH level]
        Temperature range: [Enter temperature range]
        Rainfall: [Enter average rainfall]
        Sunlight exposure: [Enter sunlight exposure]
        Ideal Environmental Conditions for Sugarcane:
        Ideal soil type: Well-drained loamy soil
        Optimal pH level: 6.0-7.5
        Ideal temperature range: 20-30°C
        Required rainfall: 1500-2500 mm annually
        Optimal sunlight exposure: Full sun
        Comparison and Recommendations:
        Compare current conditions with ideal conditions
        If current conditions match ideal conditions:
        "The current environmental conditions are excellent for the growth of sugarcane. No changes needed."
        If current conditions do not match ideal conditions:
        "To achieve optimal growth for sugarcane, consider the following recommendations:"
        Soil type: If the soil is not well-drained loamy soil, improve drainage and add organic matter to enhance soil texture.
        pH level: If the pH level is outside the range of 6.0-7.5, adjust the soil pH by adding lime to raise the pH or sulfur to lower the pH.
        Temperature: If the temperature range is not within 20-30°C, use practices like mulching to manage soil temperature or provide shade during extreme heat.
        Rainfall: If the rainfall is below 1500 mm or above 2500 mm annually, implement an irrigation system or drainage system as needed.
        Sunlight: Ensure the crop receives full sun exposure, and clear any obstructions that may block sunlight.''')
        html_content = markdown2.markdown(response.text)
        return render(request,'care_advisor.html',{'solution':html_content})
    return render(request,'care_advisor.html')