import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay, 
                           classification_report, precision_recall_curve,
                           roc_curve, auc, precision_score, recall_score, 
                           f1_score, accuracy_score)
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import warnings
import os
from datetime import datetime

# Set up matplotlib for better plots
plt.style.use('seaborn-v0_8')
warnings.filterwarnings('ignore')

# Create results directory if it doesn't exist
if not os.path.exists('model_results'):
    os.makedirs('model_results')

def load_and_preprocess_data():
    """Load and preprocess the phishing detection dataset"""
    print("Loading and preprocessing data...")
    
    # Load datasets
    phishing_df = pd.read_csv(r'phishing_domains.csv')
    legitimate_df = pd.read_csv(r'legit_domains.csv')
    
    # Combine datasets
    data = pd.concat([legitimate_df, phishing_df])
    
    # Drop specified columns
    data = data.drop(['url','NonStdPort','GoogleIndex','double_slash_redirecting','https_token'],axis=1)
    
    # Convert non-numeric columns to numeric
    non_numeric_cols = data.select_dtypes(exclude=['number']).columns.tolist()
    data[non_numeric_cols] = data[non_numeric_cols].apply(pd.to_numeric, errors='coerce')
    data.dropna(inplace=True)
    
    # Separate features and target
    X = data.drop('Label', axis=1)
    y = data['Label']
    
    print(f"Dataset shape: {data.shape}")
    print(f"Features shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts()}")
    
    return X, y, data

def create_model(input_shape):
    """Create and compile the neural network model"""
    model = keras.Sequential([
        layers.BatchNormalization(input_shape=input_shape),
        layers.Dense(130, activation='sigmoid'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(128, activation='relu'), 
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(1, activation='sigmoid'),
    ])
    
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.BinaryCrossentropy(),
                  metrics=['binary_accuracy'])
    
    return model

def plot_training_history(history, precision_history, recall_history):
    """Plot training accuracy, loss, precision, and recall curves"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot accuracy
    ax1.plot(history.history['binary_accuracy'], label='Training Accuracy', linewidth=2)
    ax1.plot(history.history['val_binary_accuracy'], label='Validation Accuracy', linewidth=2)
    ax1.set_title('Model Accuracy', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot loss
    ax2.plot(history.history['loss'], label='Training Loss', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
    ax2.set_title('Model Loss', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot precision
    ax3.plot(precision_history['train'], label='Training Precision', linewidth=2)
    ax3.plot(precision_history['val'], label='Validation Precision', linewidth=2)
    ax3.set_title('Model Precision', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Precision')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot recall
    ax4.plot(recall_history['train'], label='Training Recall', linewidth=2)
    ax4.plot(recall_history['val'], label='Validation Recall', linewidth=2)
    ax4.set_title('Model Recall', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Epoch')
    ax4.set_ylabel('Recall')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('model_results/training_history.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_confusion_matrix(y_true, y_pred):
    """Plot confusion matrix with accuracy in title"""
    cm = confusion_matrix(y_true, y_pred)
    accuracy = accuracy_score(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Legitimate', 'Phishing'],
                yticklabels=['Legitimate', 'Phishing'],
                cbar_kws={'label': 'Count'})
    plt.title(f'Confusion Matrix - Current Model\nAccuracy: {accuracy:.2%}', fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    
    plt.tight_layout()
    plt.savefig('model_results/confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_precision_recall_metrics(y_true, y_pred, y_pred_proba):
    """Plot precision, recall, and ROC curves"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    pr_auc = auc(recall, precision)
    
    ax1.plot(recall, precision, linewidth=2, label=f'PR Curve (AUC = {pr_auc:.3f})')
    ax1.set_xlabel('Recall')
    ax1.set_ylabel('Precision')
    ax1.set_title('Precision-Recall Curve', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    ax2.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {roc_auc:.3f})')
    ax2.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax2.set_xlabel('False Positive Rate')
    ax2.set_ylabel('True Positive Rate')
    ax2.set_title('ROC Curve', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Metrics Bar Chart
    metrics = {
        'Accuracy': accuracy_score(y_true, y_pred),
        'Precision': precision_score(y_true, y_pred),
        'Recall': recall_score(y_true, y_pred),
        'F1-Score': f1_score(y_true, y_pred)
    }
    
    bars = ax3.bar(metrics.keys(), metrics.values(), 
                   color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
    ax3.set_title('Model Performance Metrics', fontweight='bold')
    ax3.set_ylabel('Score')
    ax3.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, value in zip(bars, metrics.values()):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Class Distribution
    class_counts = pd.Series(y_true).value_counts()
    ax4.pie(class_counts.values, labels=['Legitimate', 'Phishing'], 
            autopct='%1.1f%%', startangle=90, colors=['lightblue', 'lightcoral'])
    ax4.set_title('Class Distribution in Test Set', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('model_results/performance_metrics.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return metrics

def calculate_feature_importance(model, X_train, y_train, X_test, y_test, feature_names):
    """Calculate and plot feature importance using a simpler approach"""
    print("Calculating feature importance...")
    
    # Calculate baseline accuracy
    baseline_pred = model.predict(X_test)
    baseline_accuracy = accuracy_score(y_test, (baseline_pred > 0.5).astype(int))
    
    # Calculate importance by feature shuffling
    importances = []
    for i, feature in enumerate(feature_names):
        # Make a copy of test data
        X_test_shuffled = X_test.copy()
        
        # Shuffle the feature
        X_test_shuffled.iloc[:, i] = np.random.permutation(X_test_shuffled.iloc[:, i])
        
        # Calculate new accuracy
        shuffled_pred = model.predict(X_test_shuffled)
        shuffled_accuracy = accuracy_score(y_test, (shuffled_pred > 0.5).astype(int))
        
        # Importance is the drop in accuracy
        importance = baseline_accuracy - shuffled_accuracy
        importances.append(importance)
    
    # Create feature importance dataframe
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    # Get top 15 features
    top_15 = importance_df.head(15).sort_values('importance', ascending=True)
    
    # Plot feature importance
    plt.figure(figsize=(12, 8))
    y_pos = np.arange(len(top_15))
    
    bars = plt.barh(y_pos, top_15['importance'], color='steelblue', alpha=0.8)
    
    plt.yticks(y_pos, top_15['feature'])
    plt.xlabel('Feature Importance')
    plt.title('Top 15 Most Important Features', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('model_results/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return importance_df

def generate_model_report(metrics, importance_df, history):
    """Generate a comprehensive model report"""
    report = f"""
    PHISHING DOMAIN DETECTION MODEL REPORT
    =====================================
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    MODEL ARCHITECTURE:
    - Input Layer: BatchNormalization
    - Hidden Layer 1: Dense(130, sigmoid) + BatchNorm + Dropout(0.4)
    - Hidden Layer 2: Dense(256, relu) + BatchNorm + Dropout(0.4)
    - Hidden Layer 3: Dense(128, relu) + BatchNorm + Dropout(0.4)
    - Output Layer: Dense(1, sigmoid)
    
    TRAINING CONFIGURATION:
    - Optimizer: Adam
    - Loss Function: Binary Crossentropy
    - Epochs: {len(history.history['loss'])}
    - Validation Split: 25%
    
    PERFORMANCE METRICS:
    - Accuracy: {metrics['Accuracy']:.4f} ({metrics['Accuracy']*100:.2f}%)
    - Precision: {metrics['Precision']:.4f}
    - Recall: {metrics['Recall']:.4f}
    - F1-Score: {metrics['F1-Score']:.4f}
    
    FINAL TRAINING METRICS:
    - Final Training Accuracy: {history.history['binary_accuracy'][-1]:.4f}
    - Final Validation Accuracy: {history.history['val_binary_accuracy'][-1]:.4f}
    - Final Training Loss: {history.history['loss'][-1]:.4f}
    - Final Validation Loss: {history.history['val_loss'][-1]:.4f}
    
    TOP 10 MOST IMPORTANT FEATURES:
    """
    
    for i, (_, row) in enumerate(importance_df.head(10).iterrows(), 1):
        report += f"    {i:2d}. {row['feature']:25s} - {row['importance']:.6f}\n"
    
    # Save report
    with open('model_results/model_report.txt', 'w') as f:
        f.write(report)
    
    print(report)

class MetricsCallback(keras.callbacks.Callback):
    """Custom callback to track precision and recall during training"""
    def __init__(self, train_data, validation_data):
        super().__init__()
        self.train_data = train_data
        self.validation_data = validation_data
        self.precision_history = {'train': [], 'val': []}
        self.recall_history = {'train': [], 'val': []}
    
    def on_epoch_end(self, epoch, logs=None):
        # Training metrics
        train_pred = (self.model.predict(self.train_data[0], verbose=0) > 0.5).astype(int)
        train_precision = precision_score(self.train_data[1], train_pred)
        train_recall = recall_score(self.train_data[1], train_pred)
        
        # Validation metrics
        val_pred = (self.model.predict(self.validation_data[0], verbose=0) > 0.5).astype(int)
        val_precision = precision_score(self.validation_data[1], val_pred)
        val_recall = recall_score(self.validation_data[1], val_pred)
        
        self.precision_history['train'].append(train_precision)
        self.precision_history['val'].append(val_precision)
        self.recall_history['train'].append(train_recall)
        self.recall_history['val'].append(val_recall)

def main():
    """Main function to run the complete model training and analysis"""
    print("=== PHISHING DOMAIN DETECTION MODEL TRAINING & ANALYSIS ===\n")
    
    # Load and preprocess data
    X, y, data = load_and_preprocess_data()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=0, stratify=y
    )
    
    # Further split training data for validation
    X_train_final, X_val, y_train_final, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=0, stratify=y_train
    )
    
    print(f"\nTraining set size: {X_train_final.shape[0]}")
    print(f"Validation set size: {X_val.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")
    
    # Create model
    input_shape = [X_train_final.shape[1]]
    model = create_model(input_shape)
    
    print(f"\nModel created with input shape: {input_shape}")
    print("Model Summary:")
    model.summary()
    
    # Create custom callback for precision/recall tracking
    metrics_callback = MetricsCallback((X_train_final, y_train_final), (X_val, y_val))
    
    # Train model
    print("\nTraining model...")
    history = model.fit(
        X_train_final, y_train_final,
        epochs=50,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[metrics_callback],
        verbose=1
    )
    
    # Save model
    model.save("NewModel.h5")
    print("\nModel saved as 'NewModel.h5'")
    
    # Make predictions
    print("\nMaking predictions...")
    y_pred_proba = model.predict(X_test).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Generate all visualizations
    print("\nGenerating visualizations...")
    
    # 1. Training history plots
    plot_training_history(history, metrics_callback.precision_history, metrics_callback.recall_history)
    
    # 2. Confusion matrix
    plot_confusion_matrix(y_test, y_pred)
    
    # 3. Performance metrics
    metrics = plot_precision_recall_metrics(y_test, y_pred, y_pred_proba)
    
    # 4. Feature importance
    importance_df = calculate_feature_importance(model, X_train_final, y_train_final, X_test, y_test, X.columns)
    
    # 5. Generate comprehensive report
    generate_model_report(metrics, importance_df, history)
    
    print(f"\n=== ANALYSIS COMPLETE ===")
    print(f"All results saved in 'model_results/' directory")
    print(f"Final Model Accuracy: {metrics['Accuracy']:.4f} ({metrics['Accuracy']*100:.2f}%)")
    
    return model, history, metrics, importance_df

# Run the complete analysis
if __name__ == "__main__":
    model, history, metrics, importance_df = main()