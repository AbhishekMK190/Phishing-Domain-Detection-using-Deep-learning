"""
Dual Model Handler for Phishing Detection System
Manages both fast model (for extension) and accurate model (for website)
"""

import tensorflow as tf
import pickle
import joblib
import numpy as np
import json
import os
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class DualModelHandler:
    def __init__(self):
        self.fast_model = None
        self.accurate_model = None
        self.fast_model_type = None
        self.fast_model_metadata = None
        self.model_lock = Lock()
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load both fast and accurate models"""
        try:
            # Load accurate model (existing deep learning model)
            logger.info("Loading accurate model...")
            self.accurate_model = tf.keras.models.load_model("my_model.h5", compile=False)
            self.accurate_model.compile(
                optimizer='adam',
                loss=tf.keras.losses.BinaryCrossentropy(reduction='sum_over_batch_size'),
                metrics=['binary_accuracy']
            )
            logger.info("Accurate model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load accurate model: {e}")
            self.accurate_model = None

        try:
            # Load fast model metadata
            if os.path.exists('fast_model_metadata.json'):
                with open('fast_model_metadata.json', 'r') as f:
                    self.fast_model_metadata = json.load(f)
                    self.fast_model_type = self.fast_model_metadata.get('model_type', 'unknown')
                    logger.info(f"Fast model type: {self.fast_model_type}")

            # Load fast model based on type
            if self.fast_model_type == 'random_forest':
                logger.info("Loading Random Forest fast model...")
                if os.path.exists('fast_model.pkl'):
                    self.fast_model = joblib.load('fast_model.pkl')
                elif os.path.exists('fast_model_rf.pkl'):
                    with open('fast_model_rf.pkl', 'rb') as f:
                        self.fast_model = pickle.load(f)
                else:
                    raise FileNotFoundError("No Random Forest model file found")

            elif self.fast_model_type == 'fast_nn':
                logger.info("Loading Neural Network fast model...")
                if os.path.exists('fast_model.h5'):
                    self.fast_model = tf.keras.models.load_model("fast_model.h5", compile=False)
                    self.fast_model.compile(
                        optimizer='adam',
                        loss='binary_crossentropy',
                        metrics=['binary_accuracy']
                    )
                else:
                    logger.warning("Fast neural network model file not found")
                    self.fast_model = None
            else:
                logger.warning("No fast model found, will use accurate model for all requests")

            if self.fast_model is not None:
                logger.info("Fast model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load fast model: {e}")
            self.fast_model = None
    
    def predict_fast(self, features):
        """
        Fast prediction for browser extension
        Optimized for speed over accuracy
        """
        if self.fast_model is None:
            # Fallback to accurate model
            return self.predict_accurate(features)

        with self.model_lock:
            try:
                start_time = time.time()

                # Ensure features is numpy array
                if not isinstance(features, np.ndarray):
                    features = np.array(features, dtype=np.float32)

                if len(features.shape) == 1:
                    features = features.reshape(1, -1)

                if self.fast_model_type == 'random_forest':
                    # Random Forest prediction
                    prediction = self.fast_model.predict_proba(features)[0][1]  # Get probability of class 1
                else:
                    # Neural Network prediction
                    prediction = float(self.fast_model.predict(features, verbose=0)[0][0])

                prediction_time = time.time() - start_time

                return {
                    'score': float(prediction),
                    'model_type': 'fast',
                    'model_name': self.fast_model_type,
                    'prediction_time_ms': prediction_time * 1000,
                    'optimized_for': 'speed'
                }

            except Exception as e:
                logger.error(f"Fast model prediction failed: {e}")
                # Fallback to accurate model
                return self.predict_accurate(features)
    
    def predict_accurate(self, features):
        """
        Accurate prediction for website interface
        Optimized for accuracy over speed
        """
        if self.accurate_model is None:
            raise RuntimeError("Accurate model not available")

        with self.model_lock:
            try:
                start_time = time.time()

                # Ensure features is numpy array
                if not isinstance(features, np.ndarray):
                    features = np.array(features, dtype=np.float32)

                if len(features.shape) == 1:
                    features = features.reshape(1, -1)

                prediction = float(self.accurate_model.predict(features, verbose=0)[0][0])
                prediction_time = time.time() - start_time

                return {
                    'score': float(prediction),
                    'model_type': 'accurate',
                    'model_name': 'deep_neural_network',
                    'prediction_time_ms': prediction_time * 1000,
                    'optimized_for': 'accuracy'
                }

            except Exception as e:
                logger.error(f"Accurate model prediction failed: {e}")
                raise
    
    def get_model_info(self):
        """Get information about loaded models"""
        info = {
            'accurate_model': {
                'available': self.accurate_model is not None,
                'type': 'deep_neural_network',
                'optimized_for': 'accuracy',
                'use_case': 'website_detailed_analysis'
            },
            'fast_model': {
                'available': self.fast_model is not None,
                'type': self.fast_model_type,
                'optimized_for': 'speed',
                'use_case': 'browser_extension_realtime',
                'metadata': self.fast_model_metadata
            }
        }
        return info
    
    def benchmark_models(self, test_features, num_runs=100):
        """Benchmark both models for performance comparison"""
        results = {}
        
        if not isinstance(test_features, np.ndarray):
            test_features = np.array(test_features, dtype=np.float32)
        
        if len(test_features.shape) == 1:
            test_features = test_features.reshape(1, -1)
        
        # Benchmark fast model
        if self.fast_model is not None:
            fast_times = []
            for _ in range(num_runs):
                start = time.time()
                self.predict_fast(test_features)
                fast_times.append((time.time() - start) * 1000)
            
            results['fast_model'] = {
                'avg_time_ms': np.mean(fast_times),
                'min_time_ms': np.min(fast_times),
                'max_time_ms': np.max(fast_times),
                'std_time_ms': np.std(fast_times)
            }
        
        # Benchmark accurate model
        if self.accurate_model is not None:
            accurate_times = []
            for _ in range(num_runs):
                start = time.time()
                self.predict_accurate(test_features)
                accurate_times.append((time.time() - start) * 1000)
            
            results['accurate_model'] = {
                'avg_time_ms': np.mean(accurate_times),
                'min_time_ms': np.min(accurate_times),
                'max_time_ms': np.max(accurate_times),
                'std_time_ms': np.std(accurate_times)
            }
        
        return results

# Global instance
_dual_model_handler = None

def get_dual_model_handler():
    """Get or create the global dual model handler instance"""
    global _dual_model_handler
    if _dual_model_handler is None:
        _dual_model_handler = DualModelHandler()
    return _dual_model_handler

def predict_with_fast_model(features):
    """Convenience function for fast prediction"""
    handler = get_dual_model_handler()
    return handler.predict_fast(features)

def predict_with_accurate_model(features):
    """Convenience function for accurate prediction"""
    handler = get_dual_model_handler()
    return handler.predict_accurate(features)
