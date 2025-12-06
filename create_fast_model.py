"""
Fast Lightweight Model Creation for Browser Extension
Creates a smaller, faster model optimized for real-time phishing detection
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import joblib
import time

def load_and_prepare_data():
    """Load and prepare the dataset"""
    print("Loading dataset...")
    
    # Load datasets
    legit_df = pd.read_csv('dataset/legit_domains.csv')
    phishing_df = pd.read_csv('dataset/phishing_domains.csv')
    
    print(f"Legitimate domains: {len(legit_df)}")
    print(f"Phishing domains: {len(phishing_df)}")
    
    # Combine datasets
    data = pd.concat([legit_df, phishing_df], ignore_index=True)
    
    # Remove problematic features (same as original model)
    data = data.drop(['url','NonStdPort','GoogleIndex','double_slash_redirecting','https_token'], axis=1)
    
    # Convert non-numeric columns
    non_numeric_cols = data.select_dtypes(exclude=['number']).columns.tolist()
    data[non_numeric_cols] = data[non_numeric_cols].apply(pd.to_numeric, errors='coerce')
    data.dropna(inplace=True)
    
    # Prepare features and labels
    X = data.drop('Label', axis=1)
    y = data['Label']
    
    print(f"Final dataset shape: {X.shape}")
    print(f"Features: {X.shape[1]}")
    
    return X, y

def create_fast_neural_network(input_shape):
    """Create a lightweight neural network for fast inference"""
    model = keras.Sequential([
        layers.BatchNormalization(input_shape=[input_shape]),
        layers.Dense(32, activation='relu'),           # Much smaller than original (130)
        layers.Dropout(0.3),                          # Less dropout
        layers.Dense(16, activation='relu'),           # Smaller hidden layer
        layers.Dropout(0.2),
        layers.Dense(1, activation='sigmoid')          # Output layer
    ])
    
    # Compile with faster optimizer settings
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['binary_accuracy']
    )
    
    return model

def create_random_forest_model():
    """Create a Random Forest model (very fast for inference)"""
    # Optimized for speed vs accuracy balance
    model = RandomForestClassifier(
        n_estimators=50,        # Fewer trees for speed
        max_depth=10,           # Limit depth for speed
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1               # Use all CPU cores
    )
    return model

def train_and_evaluate_models(X, y):
    """Train both fast models and compare performance"""
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    
    results = {}
    
    # 1. Train Fast Neural Network
    print("\n" + "="*50)
    print("Training Fast Neural Network...")
    print("="*50)
    
    fast_nn = create_fast_neural_network(X_train.shape[1])
    
    start_time = time.time()
    history = fast_nn.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=20,              # Fewer epochs for speed
        batch_size=128,         # Larger batch size for speed
        verbose=1
    )
    nn_train_time = time.time() - start_time
    
    # Evaluate Neural Network
    start_time = time.time()
    nn_predictions = fast_nn.predict(X_test)
    nn_pred_time = time.time() - start_time
    
    nn_pred_binary = (nn_predictions > 0.5).astype(int)
    nn_accuracy = accuracy_score(y_test, nn_pred_binary)
    
    print(f"\nFast Neural Network Results:")
    print(f"Training time: {nn_train_time:.2f} seconds")
    print(f"Prediction time: {nn_pred_time:.4f} seconds ({len(X_test)} samples)")
    print(f"Accuracy: {nn_accuracy:.4f}")
    print(f"Average prediction time per sample: {(nn_pred_time/len(X_test))*1000:.2f} ms")
    
    results['fast_nn'] = {
        'model': fast_nn,
        'accuracy': nn_accuracy,
        'train_time': nn_train_time,
        'pred_time': nn_pred_time,
        'avg_pred_time_ms': (nn_pred_time/len(X_test))*1000
    }
    
    # 2. Train Random Forest
    print("\n" + "="*50)
    print("Training Random Forest...")
    print("="*50)
    
    rf_model = create_random_forest_model()
    
    start_time = time.time()
    rf_model.fit(X_train, y_train)
    rf_train_time = time.time() - start_time
    
    # Evaluate Random Forest
    start_time = time.time()
    rf_predictions = rf_model.predict(X_test)
    rf_pred_time = time.time() - start_time
    
    rf_accuracy = accuracy_score(y_test, rf_predictions)
    
    print(f"\nRandom Forest Results:")
    print(f"Training time: {rf_train_time:.2f} seconds")
    print(f"Prediction time: {rf_pred_time:.4f} seconds ({len(X_test)} samples)")
    print(f"Accuracy: {rf_accuracy:.4f}")
    print(f"Average prediction time per sample: {(rf_pred_time/len(X_test))*1000:.2f} ms")
    
    results['random_forest'] = {
        'model': rf_model,
        'accuracy': rf_accuracy,
        'train_time': rf_train_time,
        'pred_time': rf_pred_time,
        'avg_pred_time_ms': (rf_pred_time/len(X_test))*1000
    }
    
    # 3. Load and test original model for comparison
    print("\n" + "="*50)
    print("Testing Original Model (for comparison)...")
    print("="*50)
    
    try:
        original_model = tf.keras.models.load_model("my_model.h5", compile=False)
        original_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['binary_accuracy'])
        
        start_time = time.time()
        orig_predictions = original_model.predict(X_test)
        orig_pred_time = time.time() - start_time
        
        orig_pred_binary = (orig_predictions > 0.5).astype(int)
        orig_accuracy = accuracy_score(y_test, orig_pred_binary)
        
        print(f"\nOriginal Model Results:")
        print(f"Prediction time: {orig_pred_time:.4f} seconds ({len(X_test)} samples)")
        print(f"Accuracy: {orig_accuracy:.4f}")
        print(f"Average prediction time per sample: {(orig_pred_time/len(X_test))*1000:.2f} ms")
        
        results['original'] = {
            'model': original_model,
            'accuracy': orig_accuracy,
            'pred_time': orig_pred_time,
            'avg_pred_time_ms': (orig_pred_time/len(X_test))*1000
        }
        
    except Exception as e:
        print(f"Could not load original model: {e}")
    
    return results, X_test, y_test

def save_best_fast_model(results):
    """Save the best performing fast model"""
    
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    
    for name, result in results.items():
        print(f"{name.upper()}:")
        print(f"  Accuracy: {result['accuracy']:.4f}")
        print(f"  Avg Prediction Time: {result['avg_pred_time_ms']:.2f} ms")
        if 'train_time' in result:
            print(f"  Training Time: {result['train_time']:.2f} seconds")
        print()
    
    # Choose the best model based on speed-accuracy tradeoff
    # Prioritize models under 10ms prediction time with good accuracy
    fast_models = {k: v for k, v in results.items() if k != 'original'}
    
    best_model = None
    best_name = None
    best_score = 0
    
    for name, result in fast_models.items():
        # Score = accuracy - (prediction_time_penalty)
        # Penalize models that take more than 5ms per prediction
        time_penalty = max(0, (result['avg_pred_time_ms'] - 5) * 0.01)
        score = result['accuracy'] - time_penalty
        
        print(f"{name} score: {score:.4f} (accuracy: {result['accuracy']:.4f}, time_penalty: {time_penalty:.4f})")
        
        if score > best_score:
            best_score = score
            best_model = result['model']
            best_name = name
    
    print(f"\nBest fast model: {best_name}")
    
    # Save the best fast model
    if best_name == 'random_forest':
        joblib.dump(best_model, 'fast_model.pkl')
        print("Saved Random Forest model as 'fast_model.pkl'")
        
        # Also save as pickle for compatibility
        with open('fast_model_rf.pkl', 'wb') as f:
            pickle.dump(best_model, f)
            
    else:  # Neural network
        best_model.save('fast_model.h5')
        print("Saved Neural Network model as 'fast_model.h5'")
    
    # Save model metadata
    metadata = {
        'model_type': best_name,
        'accuracy': results[best_name]['accuracy'],
        'avg_prediction_time_ms': results[best_name]['avg_pred_time_ms'],
        'recommended_for': 'browser_extension',
        'created_at': pd.Timestamp.now().isoformat()
    }
    
    with open('fast_model_metadata.json', 'w') as f:
        import json
        json.dump(metadata, f, indent=2)
    
    return best_name, best_model, metadata

def main():
    print("Creating Fast Model for Browser Extension")
    print("="*50)
    
    # Load data
    X, y = load_and_prepare_data()
    
    # Train and evaluate models
    results, X_test, y_test = train_and_evaluate_models(X, y)
    
    # Save the best model
    best_name, best_model, metadata = save_best_fast_model(results)
    
    print("\n" + "="*60)
    print("FAST MODEL CREATION COMPLETE")
    print("="*60)
    print(f"Best model: {best_name}")
    print(f"Accuracy: {metadata['accuracy']:.4f}")
    print(f"Speed: {metadata['avg_prediction_time_ms']:.2f} ms per prediction")
    print("\nFiles created:")
    if best_name == 'random_forest':
        print("- fast_model.pkl (main model file)")
        print("- fast_model_rf.pkl (backup)")
    else:
        print("- fast_model.h5 (neural network)")
    print("- fast_model_metadata.json (model info)")
    
    print(f"\nRecommendation: Use {best_name} for browser extension")
    print("This model prioritizes speed for real-time protection.")

if __name__ == "__main__":
    main()
