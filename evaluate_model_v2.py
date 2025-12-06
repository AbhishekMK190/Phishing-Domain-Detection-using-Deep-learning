import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set(font_scale=1.2)

def load_model(model_path):
    """Load the trained model and print its architecture"""
    print(f"Loading model from {model_path}...")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file {model_path} not found!")
    
    model = tf.keras.models.load_model(model_path)
    print("Model loaded successfully!")
    return model

def load_and_prepare_data(legit_path, phishing_path, sample_size=100):
    """Load and prepare test data matching the training data format"""
    print("\nLoading datasets...")
    
    # Load datasets with explicit data types to avoid mixed type warnings
    legit_df = pd.read_csv(legit_path, low_memory=False)
    phishing_df = pd.read_csv(phishing_path, low_memory=False)
    
    print(f"Loaded {len(legit_df)} legitimate and {len(phishing_df)} phishing samples")
    
    # Sample equal number of legitimate and phishing domains
    legit_sample = legit_df.sample(min(sample_size, len(legit_df)), random_state=42)
    phishing_sample = phishing_df.sample(min(sample_size, len(phishing_df)), random_state=42)
    
    # Columns to drop (must match what was used during training)
    columns_to_drop = ['url', 'Label', 'NonStdPort', 'GoogleIndex', 'double_slash_redirecting', 'https_token']
    
    # Prepare features and labels
    X_legit = legit_sample.drop(columns=[col for col in columns_to_drop if col in legit_sample.columns], errors='ignore')
    X_phish = phishing_sample.drop(columns=[col for col in columns_to_drop if col in phishing_sample.columns], errors='ignore')
    
    # Ensure all features are numeric
    for df in [X_legit, X_phish]:
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create labels (0 for legitimate, 1 for phishing)
    y_legit = np.zeros(len(X_legit))
    y_phish = np.ones(len(X_phish))
    
    # Combine data
    X = pd.concat([X_legit, X_phish], axis=0)
    y = np.concatenate([y_legit, y_phish])
    
    # Fill any remaining NaN values with 0
    X = X.fillna(0)
    
    print(f"Final dataset shape: {X.shape} (features: {X.shape[1]}, samples: {X.shape[0]})")
    print(f"Class distribution: {len(y_legit)} legitimate, {len(y_phish)} phishing")
    
    return X, y, legit_sample, phishing_sample

def evaluate_model(model, X_test, y_test):
    """Evaluate model and return metrics"""
    print("\nEvaluating model...")
    
    # Make predictions
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred),
        'y_true': y_test,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba
    }
    
    return metrics

def plot_confusion_matrix(cm, classes, filename='confusion_matrix.png'):
    """Plot and save confusion matrix"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Confusion matrix saved as {filename}")

def print_metrics(metrics):
    """Print evaluation metrics in a readable format"""
    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS")
    print("="*50)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(metrics['y_true'], metrics['y_pred'], 
                              target_names=['Legitimate', 'Phishing']))
    
    print("\nConfusion Matrix:")
    print(metrics['confusion_matrix'])

def main():
    # Configuration
    config = {
        'model_path': 'my_model.h5',
        'legit_paths': [
            'dataset/legit_domains.csv', 
            'legit_domains.csv',
            'dataset/legitimate_domains.csv',
            'legitimate_domains.csv'
        ],
        'phishing_paths': [
            'dataset/phishing_domains.csv',
            'phishing_domains.csv',
            'dataset/malicious_domains.csv',
            'malicious_domains.csv'
        ],
        'sample_size': 100
    }
    
    # Find dataset files
    print("Looking for dataset files...")
    legit_path = next((p for p in config['legit_paths'] if os.path.exists(p)), None)
    phishing_path = next((p for p in config['phishing_paths'] if os.path.exists(p)), None)
    
    if not legit_path or not phishing_path:
        print("\nError: Could not find dataset files. Please make sure the CSV files exist in one of these locations:")
        print("Legitimate domains:", config['legit_paths'])
        print("Phishing domains:", config['phishing_paths'])
        return
    
    print(f"\nFound datasets:")
    print(f"- Legitimate: {legit_path}")
    print(f"- Phishing: {phishing_path}")
    
    try:
        # Load and prepare data
        X_test, y_test, legit_samples, phish_samples = load_and_prepare_data(
            legit_path, phishing_path, config['sample_size']
        )
        
        # Load model
        model = load_model(config['model_path'])
        
        # Print model summary
        print("\nModel architecture:")
        model.summary()
        
        # Check input shape
        input_shape = model.input_shape[1:]
        print(f"\nModel expects input shape: {input_shape}")
        print(f"Test data shape: {X_test.shape}")
        
        # Ensure input dimensions match
        if len(input_shape) > 1 and X_test.shape[1] != input_shape[0]:
            print(f"\nWarning: Input shape mismatch. Expected {input_shape[0]} features, got {X_test.shape[1]}.")
            print("Trying to adjust input data...")
            
            # If we have more features than expected, take the first n
            if X_test.shape[1] > input_shape[0]:
                X_test = X_test.iloc[:, :input_shape[0]]
                print(f"Using first {input_shape[0]} features.")
            # If we have fewer features, pad with zeros
            elif X_test.shape[1] < input_shape[0]:
                padding = np.zeros((len(X_test), input_shape[0] - X_test.shape[1]))
                X_test = np.hstack([X_test, padding])
                print(f"Padded input with {input_shape[0] - X_test.shape[1]} zeros.")
        
        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test)
        
        # Print and plot results
        print_metrics(metrics)
        plot_confusion_matrix(metrics['confusion_matrix'], ['Legitimate', 'Phishing'])
        
        print("\nEvaluation complete! Check 'confusion_matrix.png' for visualization.")
        
    except Exception as e:
        print(f"\nError during evaluation: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
