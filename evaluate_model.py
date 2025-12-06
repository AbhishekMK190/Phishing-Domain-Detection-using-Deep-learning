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

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set(font_scale=1.2)

def load_model(model_path='my_model.h5'):
    """Load the trained model"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file {model_path} not found!")
    return tf.keras.models.load_model(model_path)

def load_test_data(legit_path, phishing_path, sample_size=100):
    """Load and prepare test data"""
    # Load datasets with proper data types
    legit_df = pd.read_csv(legit_path, low_memory=False)
    phishing_df = pd.read_csv(phishing_path, low_memory=False)
    
    # Sample equal number of legitimate and phishing domains
    legit_sample = legit_df.sample(min(sample_size, len(legit_df)), random_state=42)
    phishing_sample = phishing_df.sample(min(sample_size, len(phishing_df)), random_state=42)
    
    # Combine and prepare data - match the same columns used during training
    # First get the columns we need based on the model's expected input shape
    # These are the columns that were used during training (from model.py)
    columns_to_drop = ['url', 'Label', 'NonStdPort', 'GoogleIndex', 'double_slash_redirecting', 'https_token']
    
    X_legit = legit_sample.drop(columns=[col for col in columns_to_drop if col in legit_sample.columns], errors='ignore')
    X_phish = phishing_sample.drop(columns=[col for col in columns_to_drop if col in phishing_sample.columns], errors='ignore')
    
    # Create labels (0 for legitimate, 1 for phishing)
    y_legit = np.zeros(len(X_legit))
    y_phish = np.ones(len(X_phish))
    
    # Combine data
    X = pd.concat([X_legit, X_phish], axis=0)
    y = np.concatenate([y_legit, y_phish])
    
    # Convert non-numeric columns to numeric
    non_numeric_cols = X.select_dtypes(exclude=['number']).columns.tolist()
    if non_numeric_cols:
        X[non_numeric_cols] = X[non_numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Handle any remaining non-numeric values
    X = X.astype(float)
    
    return X, y, legit_sample, phishing_sample

def evaluate_model(model, X_test, y_test):
    """Evaluate model and return metrics"""
    # Make predictions
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'y_true': y_test,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba
    }

def plot_confusion_matrix(cm, classes):
    """Plot confusion matrix"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()

def print_metrics(metrics):
    """Print evaluation metrics"""
    print("\n" + "="*50)
    print("MODEL EVALUATION METRICS")
    print("="*50)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    print("\nClassification Report:")
    print(classification_report(metrics['y_true'], metrics['y_pred'], 
                               target_names=['Legitimate', 'Phishing']))

def main():
    # Paths
    model_path = 'my_model.h5'
    # Try both possible paths for the dataset
    legit_paths = ['dataset/legit_domains.csv', 'legit_domains.csv']
    phishing_paths = ['dataset/phishing_domains.csv', 'phishing_domains.csv']
    
    # Find the first valid path for each dataset
    legit_path = next((p for p in legit_paths if os.path.exists(p)), None)
    phishing_path = next((p for p in phishing_paths if os.path.exists(p)), None)
    
    if not legit_path or not phishing_path:
        print("Error: Could not find dataset files. Please make sure the CSV files exist.")
        print(f"Looked for legitimate domains in: {legit_paths}")
        print(f"Looked for phishing domains in: {phishing_paths}")
        return
    
    print("Loading model and data...")
    try:
        # Load model and data
        model = load_model(model_path)
        
        # Print model summary to understand input shape
        print("\nModel summary:")
        model.summary()
        
        # Get the expected input shape from the model
        expected_input_shape = model.layers[0].input_shape[1:]
        print(f"\nModel expects input shape: {expected_input_shape}")
        
        X_test, y_test, legit_samples, phish_samples = load_test_data(legit_path, phishing_path, sample_size=100)
        
        print(f"\nTesting on {len(X_test)} samples ({len(legit_samples)} legitimate, {len(phish_samples)} phishing)")
        print(f"Input data shape: {X_test.shape}")
        
        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test)
        
        # Print and plot results
        print_metrics(metrics)
        plot_confusion_matrix(metrics['confusion_matrix'], ['Legitimate', 'Phishing'])
        
        print("\nEvaluation complete! Check 'confusion_matrix.png' for visualization.")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Make sure the model and data files exist in the correct locations.")

if __name__ == "__main__":
    main()
