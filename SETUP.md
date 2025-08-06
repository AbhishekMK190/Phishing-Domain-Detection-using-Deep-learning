# Phishing Domain Detection - Setup Guide

## Overview
This project is a Flask web application that uses machine learning to detect phishing domains. It analyzes various features of websites to classify them as legitimate or phishing.

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Installation Steps

### 1. Clone or Download the Project
Make sure you have all the project files in your directory.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
The following packages should be installed:
- Flask (web framework)
- TensorFlow (machine learning)
- NumPy (numerical computing)
- Pandas (data manipulation)
- scikit-learn (machine learning utilities)
- requests (HTTP library)
- BeautifulSoup4 (HTML parsing)
- python-whois (domain information)
- dnspython (DNS utilities)
- matplotlib (plotting)

### 4. Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

### 5. Test the Application
```bash
python test_app.py
```

## How to Use

1. **Start the Application**: Run `python app.py`
2. **Open Browser**: Go to `http://localhost:5000`
3. **Enter Domain**: Type a domain name (e.g., `google.com`, `facebook.com`)
4. **Get Results**: The application will analyze the domain and show if it's legitimate or phishing

## Features Analyzed

The application analyzes 65 different features including:
- Domain characteristics (length, special characters, SSL)
- Website content (forms, links, scripts)
- DNS information (name servers, records)
- WHOIS data (domain age, registration length)
- Security indicators (redirects, executable files)

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Model Loading Error**: The application uses pre-trained models (`newModelTest.h5`). Make sure these files are present.

3. **WHOIS Errors**: Some domains may not have accessible WHOIS information. The application handles this gracefully.

4. **Network Issues**: The application needs internet access to analyze websites.

### Error Messages

- **"Unable to analyze website features"**: The website couldn't be accessed or parsed
- **"not active"**: The domain doesn't respond to HTTP requests
- **"invalid"**: The input doesn't contain a valid domain format
- **"Error during analysis"**: An error occurred during feature extraction or prediction

### URL Input Formats

The application accepts various URL formats:
- `google.com`
- `www.google.com`
- `https://google.com`
- `http://google.com`
- `https://www.google.com`
- `https://google.com/`

All formats will be automatically cleaned and normalized.

## Project Structure

```
phising-Domain-Detection-main/
├── app.py                          # Main Flask application
├── model.py                        # Model training code
├── newModelTest.h5                 # Pre-trained model
├── requirements.txt                # Python dependencies
├── test_app.py                     # Test script
├── web_scarping/
│   ├── Feature_extraction_ff1.py   # Feature extraction
│   └── feature_init_ff1.py         # Feature definitions
├── templates/
│   ├── real_index1.html           # Home page
│   └── real_result.html           # Results page
└── static/
    └── index_style.css            # CSS styles
```

## Model Information

- **Type**: Artificial Neural Network (ANN)
- **Accuracy**: ~88% on binary classification
- **Features**: 65 domain and content-based features
- **Dataset**: 26,206 legitimate + 26,352 phishing domains

## Security Note

This tool is for educational and research purposes. Always verify results with other security tools and use common sense when browsing the web.

## Support

If you encounter issues:
1. Check that all dependencies are installed
2. Ensure you have internet connectivity
3. Verify the model files are present
4. Check the console for error messages 