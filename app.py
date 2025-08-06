# app.py
from flask import Flask , render_template ,request
import requests
# import last_logic_backup
import web_scarping.Feature_extraction_ff1 as fex
import pickle
import tensorflow as tf
from tensorflow import keras
import numpy as np

app = Flask(__name__)
model = tf.keras.models.load_model("newModelTest.h5")
# model = pickle.load(open("model.h5","rb"))

@app.route("/")
def home():
    return render_template('real_index1.html')

@app.route('/check_phishing', methods=['GET', 'POST'])
def check_phishing():
    if request.method == 'POST':
        domain = request.form['url']
        if "." not in domain:
            return render_template('real_result.html', result="invalid")
        
        # Clean the domain input
        domain = domain.strip()
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = domain.split('://', 1)[1]
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing slash if present
        domain = domain.rstrip('/')
        
        print(f"Cleaned domain: {domain}")
        url = "https://" + domain
        
        try:
            response = requests.get(url, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return render_template('real_result.html', result="not active")
        if response.status_code == 200:

            try:
                new_url_features = fex.data_set_list_creation(domain)
                
                if new_url_features is None:
                    return render_template('real_result.html', result="Unable to analyze website features")

                new_url_features = np.array([new_url_features])

                prediction = model.predict(new_url_features)
                print(f"Prediction: {prediction}")
                if prediction >= 0.5:
                    print("The URL is predicted as a phishing URL.")
                    result = "The URL is predicted as a phishing URL."
                else:
                    print("The URL is predicted as a legitimate URL.")
                    result = "The URL is predicted as a legitimate URL."
                return render_template('real_result.html', result=result)
                
            except Exception as e:
                print(f"Error during analysis: {e}")
                return render_template('real_result.html', result="Error during analysis")
        else:
            return render_template('real_result.html', result="not active")

    
if __name__=='__main__':
    app.run(debug=True)