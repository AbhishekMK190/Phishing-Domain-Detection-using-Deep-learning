"""
Model Retraining Module for Phishing Detection System

This module handles continuous learning from user feedback to improve model accuracy.
It implements incremental learning and model fine-tuning based on user corrections.
"""

import sqlite3
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import os
import pickle
import logging
from datetime import datetime, timedelta
from threading import Lock
import web_scarping.Feature_extraction_ff1 as fex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelRetrainer:
    def __init__(self, db_path='predictions.db', model_path='my_model.h5', backup_path='model_backups/'):
        self.db_path = db_path
        self.model_path = model_path
        self.backup_path = backup_path
        self.lock = Lock()
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_path, exist_ok=True)
        
        # Minimum feedback threshold for retraining (reduced since we mix with original data)
        self.min_feedback_threshold = 5  # Reduced from 10
        self.disagreement_threshold = 0.50  # 50% disagreement rate triggers retraining
        
    def get_feedback_data(self, days_back=30):
        """
        Retrieve feedback data from the database for model retraining.
        
        Args:
            days_back (int): Number of days to look back for feedback data
            
        Returns:
            pandas.DataFrame: Feedback data with features and corrected labels
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Get feedback data with prediction details
                query = """
                SELECT 
                    f.domain, f.url, f.vote, f.note, f.created_at,
                    p.label as original_label, p.score as original_score
                FROM feedbacks f
                LEFT JOIN predictions p ON f.prediction_id = p.id
                WHERE f.created_at >= datetime('now', '-{} days')
                AND f.domain IS NOT NULL
                AND f.domain != ''
                ORDER BY f.created_at DESC
                """.format(days_back)
                
                df = pd.read_sql_query(query, conn)
                return df
            finally:
                conn.close()
    
    def extract_features_for_domains(self, domains):
        """
        Extract features for a list of domains using the existing feature extraction.
        
        Args:
            domains (list): List of domain names
            
        Returns:
            numpy.ndarray: Feature matrix
        """
        features = []
        valid_domains = []
        
        for domain in domains:
            try:
                # Clean domain name
                domain = domain.lower().strip()
                if domain.startswith('http://'):
                    domain = domain[7:]
                elif domain.startswith('https://'):
                    domain = domain[8:]
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                # Extract features
                domain_features = fex.data_set_list_creation(domain)
                if domain_features and len(domain_features) > 0:
                    features.append(domain_features)
                    valid_domains.append(domain)
                else:
                    logger.warning(f"Failed to extract features for domain: {domain}")
            except Exception as e:
                logger.error(f"Error extracting features for {domain}: {e}")
                continue
        
        if features:
            return np.array(features, dtype=np.float32), valid_domains
        else:
            return np.array([]), []
    
    def load_original_training_data(self, sample_size=2000):
        """
        Load a sample of the original training data to mix with feedback.
        
        Args:
            sample_size (int): Number of samples to load from original dataset
            
        Returns:
            tuple: (X_original, y_original, sample_weights_original)
        """
        try:
            # Load legitimate domains
            legit_df = pd.read_csv('dataset/legit_domains.csv')
            # Load phishing domains  
            phishing_df = pd.read_csv('dataset/phishing_domains.csv')
            
            # Sample from each dataset (balanced)
            legit_sample_size = sample_size // 2
            phishing_sample_size = sample_size // 2
            
            # Sample randomly from each dataset
            if len(legit_df) > legit_sample_size:
                legit_sample = legit_df.sample(n=legit_sample_size, random_state=42)
            else:
                legit_sample = legit_df
                
            if len(phishing_df) > phishing_sample_size:
                phishing_sample = phishing_df.sample(n=phishing_sample_size, random_state=42)
            else:
                phishing_sample = phishing_df
            
            # Combine samples
            combined_df = pd.concat([legit_sample, phishing_sample], ignore_index=True)
            
            # Extract features (exclude url and Label columns)
            feature_columns = [col for col in combined_df.columns if col not in ['url', 'Label']]
            X_original = combined_df[feature_columns].values.astype(np.float32)
            y_original = combined_df['Label'].values.astype(np.float32)
            
            # Create uniform weights for original data (lower than feedback data)
            original_weights = np.full(len(X_original), 0.3)  # Lower weight than feedback
            
            logger.info(f"Loaded {len(X_original)} samples from original dataset")
            return X_original, y_original, original_weights
            
        except Exception as e:
            logger.error(f"Failed to load original training data: {e}")
            return None, None, None

    def prepare_training_data(self, feedback_df):
        """
        Prepare mixed training data combining original dataset with feedback corrections.
        
        Args:
            feedback_df (pandas.DataFrame): Feedback data
            
        Returns:
            tuple: (X_train, y_train, sample_weights)
        """
        if feedback_df.empty:
            return None, None, None
        
        # Filter for disagreement feedback (where user corrected the model)
        disagreement_df = feedback_df[feedback_df['vote'] == 'disagree'].copy()
        
        if disagreement_df.empty:
            logger.info("No disagreement feedback found for retraining")
            return None, None, None
        
        logger.info(f"Processing {len(disagreement_df)} disagreement feedback entries")
        
        # Extract features for domains with disagreement
        domains = disagreement_df['domain'].tolist()
        X_feedback, valid_domains = self.extract_features_for_domains(domains)
        
        if len(X_feedback) == 0:
            logger.warning("No valid features extracted from feedback data")
            return None, None, None
        
        # Create corrected labels for feedback data
        y_feedback = []
        feedback_weights = []
        
        for i, domain in enumerate(valid_domains):
            domain_feedback = disagreement_df[disagreement_df['domain'] == domain].iloc[0]
            original_label = domain_feedback['original_label']
            
            # If user disagreed, flip the label
            if original_label == 'phishing':
                corrected_label = 0  # legitimate
            else:
                corrected_label = 1  # phishing
            
            y_feedback.append(corrected_label)
            
            # Higher weight for recent feedback (feedback gets priority)
            feedback_date = pd.to_datetime(domain_feedback['created_at'])
            days_old = (datetime.now() - feedback_date).days
            weight = max(1.0, 2.0 - (days_old / 30.0))  # Higher weight for feedback
            feedback_weights.append(weight)
        
        # Load original training data
        X_original, y_original, original_weights = self.load_original_training_data(
            sample_size=min(2000, len(X_feedback) * 100)  # Scale with feedback size
        )
        
        if X_original is None:
            logger.warning("Failed to load original data, using only feedback data")
            return X_feedback, np.array(y_feedback), np.array(feedback_weights)
        
        # Combine original and feedback data
        X_combined = np.vstack([X_original, X_feedback])
        y_combined = np.concatenate([y_original, np.array(y_feedback)])
        weights_combined = np.concatenate([original_weights, np.array(feedback_weights)])
        
        logger.info(f"Combined training data: {len(X_original)} original + {len(X_feedback)} feedback = {len(X_combined)} total samples")
        
        return X_combined, y_combined, weights_combined
    
    def should_retrain(self):
        """
        Determine if the model should be retrained based on feedback patterns.
        
        Returns:
            tuple: (should_retrain: bool, reason: str)
        """
        feedback_df = self.get_feedback_data(days_back=7)  # Check last 7 days
        
        if feedback_df.empty:
            return False, "No feedback data available"
        
        total_feedback = len(feedback_df)
        disagreement_count = len(feedback_df[feedback_df['vote'] == 'disagree'])
        
        if total_feedback < self.min_feedback_threshold:
            return False, f"Insufficient feedback ({total_feedback} < {self.min_feedback_threshold})"
        
        disagreement_rate = disagreement_count / total_feedback
        
        if disagreement_rate >= self.disagreement_threshold:
            return True, f"High disagreement rate: {disagreement_rate:.2%} ({disagreement_count}/{total_feedback})"
        
        return False, f"Disagreement rate acceptable: {disagreement_rate:.2%}"
    
    def backup_current_model(self):
        """Create a backup of the current model before retraining."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"model_backup_{timestamp}.h5"
        backup_path = os.path.join(self.backup_path, backup_filename)
        
        try:
            # Copy current model to backup
            import shutil
            shutil.copy2(self.model_path, backup_path)
            logger.info(f"Model backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup model: {e}")
            return None
    
    def fine_tune_model(self, X_train, y_train, sample_weights=None):
        """
        Fine-tune the existing model with new feedback data.
        
        Args:
            X_train (numpy.ndarray): Training features
            y_train (numpy.ndarray): Training labels
            sample_weights (numpy.ndarray): Sample weights for training
            
        Returns:
            tuple: (success: bool, metrics: dict)
        """
        try:
            # Load current model
            model = tf.keras.models.load_model(self.model_path, compile=False)
            
            # Recompile with lower learning rate for fine-tuning
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),  # Lower LR for fine-tuning
                loss='binary_crossentropy',
                metrics=['binary_accuracy']
            )
            
            # Split data for validation
            if len(X_train) > 4:
                X_train_split, X_val, y_train_split, y_val = train_test_split(
                    X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
                )
                if sample_weights is not None:
                    weights_train, weights_val = train_test_split(
                        sample_weights, test_size=0.2, random_state=42, stratify=y_train
                    )
                else:
                    weights_train = None
            else:
                X_train_split, X_val = X_train, X_train
                y_train_split, y_val = y_train, y_train
                weights_train = sample_weights
            
            # Fine-tune the model with mixed data
            history = model.fit(
                X_train_split, y_train_split,
                sample_weight=weights_train,
                validation_data=(X_val, y_val),
                epochs=3,  # Reduced epochs since we have more data now
                batch_size=min(64, len(X_train_split)),  # Larger batch size for stability
                verbose=1,
                shuffle=True  # Important for mixed data
            )
            
            # Evaluate on validation set
            val_predictions = model.predict(X_val)
            val_pred_binary = (val_predictions > 0.5).astype(int)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            metrics = {
                'accuracy': accuracy_score(y_val, val_pred_binary),
                'precision': precision_score(y_val, val_pred_binary, zero_division=0),
                'recall': recall_score(y_val, val_pred_binary, zero_division=0),
                'f1_score': f1_score(y_val, val_pred_binary, zero_division=0),
                'training_samples': len(X_train),
                'final_loss': history.history['loss'][-1],
                'final_val_loss': history.history['val_loss'][-1] if 'val_loss' in history.history else None
            }
            
            # Validate that the new model performs reasonably well
            if metrics['accuracy'] < 0.6:  # Minimum acceptable accuracy
                logger.warning(f"Model accuracy too low ({metrics['accuracy']:.3f}), not saving")
                return False, metrics
            
            # Save the fine-tuned model
            model.save(self.model_path)
            logger.info(f"Model fine-tuned and saved. Metrics: {metrics}")
            
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error during model fine-tuning: {e}")
            return False, {'error': str(e)}
    
    def retrain_model(self):
        """
        Main method to retrain the model based on user feedback.
        
        Returns:
            dict: Retraining results and metrics
        """
        logger.info("Starting model retraining process...")
        
        # Check if retraining is needed
        should_retrain, reason = self.should_retrain()
        if not should_retrain:
            logger.info(f"Retraining not needed: {reason}")
            return {
                'success': False,
                'reason': reason,
                'retrained': False
            }
        
        logger.info(f"Retraining triggered: {reason}")
        
        # Get feedback data
        feedback_df = self.get_feedback_data(days_back=30)
        
        # Prepare training data
        X_train, y_train, sample_weights = self.prepare_training_data(feedback_df)
        
        if X_train is None or len(X_train) == 0:
            logger.warning("No valid training data prepared from feedback")
            return {
                'success': False,
                'reason': 'No valid training data from feedback',
                'retrained': False
            }
        
        # Backup current model
        backup_path = self.backup_current_model()
        
        # Fine-tune the model
        success, metrics = self.fine_tune_model(X_train, y_train, sample_weights)
        
        result = {
            'success': success,
            'retrained': success,
            'reason': reason,
            'backup_path': backup_path,
            'training_samples': len(X_train),
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            logger.info("Model retraining completed successfully")
            # Log retraining event to database
            self._log_retraining_event(result)
        else:
            logger.error("Model retraining failed")
        
        return result
    
    def _log_retraining_event(self, result):
        """Log retraining event to database for tracking."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Create retraining log table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS retraining_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        success INTEGER,
                        training_samples INTEGER,
                        metrics TEXT,
                        reason TEXT,
                        backup_path TEXT
                    )
                """)
                
                # Insert retraining event
                conn.execute("""
                    INSERT INTO retraining_log 
                    (timestamp, success, training_samples, metrics, reason, backup_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result['timestamp'],
                    1 if result['success'] else 0,
                    result.get('training_samples', 0),
                    str(result.get('metrics', {})),
                    result['reason'],
                    result.get('backup_path', '')
                ))
                
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to log retraining event: {e}")
            finally:
                conn.close()

# Global retrainer instance
_retrainer = None

def get_retrainer():
    """Get or create the global retrainer instance."""
    global _retrainer
    if _retrainer is None:
        _retrainer = ModelRetrainer()
    return _retrainer

def trigger_model_update():
    """Trigger model update check and retraining if needed."""
    try:
        retrainer = get_retrainer()
        result = retrainer.retrain_model()
        return result
    except Exception as e:
        logger.error(f"Error in trigger_model_update: {e}")
        return {
            'success': False,
            'error': str(e),
            'retrained': False
        }
