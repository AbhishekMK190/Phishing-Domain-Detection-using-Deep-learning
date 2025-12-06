"""
Background Task Manager for Phishing Detection System

This module handles automatic model retraining and other background tasks.
It runs periodic checks and triggers retraining when needed without blocking the main Flask server.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
import model_retraining
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self, check_interval_minutes=5):
        self.check_interval_minutes = check_interval_minutes
        self.check_interval_seconds = check_interval_minutes * 60
        self.is_running = False
        self.thread = None
        self.retraining_active = False
        self.last_check = None
        self.auto_retrain_enabled = os.getenv('AUTO_RETRAIN_ENABLED', 'true').lower() == 'true'
        
    def start(self):
        """Start the background task manager."""
        if self.is_running:
            logger.warning("Background task manager is already running")
            return
            
        if not self.auto_retrain_enabled:
            logger.info("Auto-retraining is disabled via environment variable")
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run_background_tasks, daemon=True)
        self.thread.start()
        logger.info(f"Background task manager started (checking every {self.check_interval_minutes} minutes)")
        
    def stop(self):
        """Stop the background task manager."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("Background task manager stopped")
        
    def _run_background_tasks(self):
        """Main loop for background tasks."""
        while self.is_running:
            try:
                self.last_check = datetime.utcnow()
                self._check_and_retrain()
                
                # Sleep in small intervals to allow for graceful shutdown
                for _ in range(self.check_interval_seconds):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in background task loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying on error
                
    def _check_and_retrain(self):
        """Check if retraining is needed and trigger it if necessary."""
        if self.retraining_active:
            logger.info("Retraining already in progress, skipping check")
            return
            
        try:
            retrainer = model_retraining.get_retrainer()
            should_retrain, reason = retrainer.should_retrain()
            
            if should_retrain:
                logger.info(f"Auto-retraining triggered: {reason}")
                self._trigger_background_retraining()
            else:
                logger.debug(f"No retraining needed: {reason}")
                
        except Exception as e:
            logger.error(f"Error checking retraining status: {e}")
            
    def _trigger_background_retraining(self):
        """Trigger retraining in a separate thread to avoid blocking."""
        if self.retraining_active:
            logger.warning("Retraining already in progress")
            return
            
        # Start retraining in a separate thread
        retraining_thread = threading.Thread(
            target=self._run_retraining,
            daemon=True
        )
        retraining_thread.start()
        
    def _run_retraining(self):
        """Run the actual retraining process."""
        self.retraining_active = True
        try:
            logger.info("Starting background model retraining...")
            retrainer = model_retraining.get_retrainer()
            result = retrainer.retrain_model()
            
            if result.get('success'):
                logger.info(f"Background retraining completed successfully. "
                          f"Training samples: {result.get('training_samples', 0)}, "
                          f"Accuracy: {result.get('metrics', {}).get('accuracy', 0):.3f}")
            else:
                logger.warning(f"Background retraining failed or not needed: {result.get('reason', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error during background retraining: {e}")
        finally:
            self.retraining_active = False
            
    def get_status(self):
        """Get the current status of the background task manager."""
        return {
            "is_running": self.is_running,
            "auto_retrain_enabled": self.auto_retrain_enabled,
            "retraining_active": self.retraining_active,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_interval_minutes": self.check_interval_minutes,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

# Global background task manager instance
_background_manager = None

def get_background_manager():
    """Get or create the global background task manager instance."""
    global _background_manager
    if _background_manager is None:
        _background_manager = BackgroundTaskManager()
    return _background_manager

def start_background_tasks():
    """Start the background task manager."""
    manager = get_background_manager()
    manager.start()
    return manager

def stop_background_tasks():
    """Stop the background task manager."""
    global _background_manager
    if _background_manager:
        _background_manager.stop()
        _background_manager = None

def get_background_status():
    """Get the status of background tasks."""
    manager = get_background_manager()
    return manager.get_status()
