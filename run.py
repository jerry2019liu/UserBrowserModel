### export the model as API to online user 

import pandas as pd
import boto3
import json
from flask import Flask, request, jsonify
import joblib  # For loading your trained model

app = Flask(__name__)

# --- AWS Configuration (Replace with your values) ---
SAGEMAKER_ENDPOINT_NAME = 'UserBrowserModelEndpoint' # Your SageMaker endpoint name
PROFILE_NAME = None # Optional: if using named profiles
AWS_REGION = 'your_aws_region'

# --- Initialize AWS Resources ---
if PROFILE_NAME:
    session = boto3.Session(profile_name=PROFILE_NAME, region_name=AWS_REGION)
else:
    session = boto3.Session(region_name=AWS_REGION)

sagemaker_runtime = session.client('runtime.sagemaker')

# --- Model Loading (Alternative to SageMaker if needed) ---
# If your model is small and you prefer to load it directly into the Flask app, you can do this:
# model = joblib.load('model.pkl') # Load your model

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)

        # --- Input Validation ---
        if not isinstance(data, dict) or 'user_id' not in data:
            return jsonify({'error': 'Invalid input. Expected JSON with "user_id" key.'}), 400

        user_id = data['user_id']

        # --- SageMaker Inference (Preferred) ---
        # Call the SageMaker endpoint for prediction
        payload = json.dumps({'user_id': user_id}) # Adjust payload based on your model input.

        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='application/json',
            Body=payload
        )

        result = json.loads(response['Body'].read().decode())

        # --- Alternative: Local Model Inference (if model loaded locally) ---
        # user_data = pd.DataFrame({'user_id': [user_id]}) # Create input dataframe.
        # prediction = model.predict(user_data) # Make prediction
        # result = {'prediction': prediction.tolist()} # Format the result

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) # Ensure 0.0.0.0 for external access.
