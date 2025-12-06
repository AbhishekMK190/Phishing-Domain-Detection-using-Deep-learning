"""
Test script for mixed training implementation
"""
import model_retraining
import pandas as pd
import numpy as np

def test_mixed_training():
    print("=== Testing Mixed Training Implementation ===\n")
    
    # Initialize retrainer
    retrainer = model_retraining.ModelRetrainer()
    
    # Test 1: Load original training data
    print("1. Testing original data loading...")
    try:
        X_orig, y_orig, weights_orig = retrainer.load_original_training_data(sample_size=100)
        if X_orig is not None:
            print(f"✅ Successfully loaded {len(X_orig)} original samples")
            print(f"   Features shape: {X_orig.shape}")
            print(f"   Labels distribution: {np.bincount(y_orig.astype(int))}")
            print(f"   Sample weights range: {weights_orig.min():.2f} - {weights_orig.max():.2f}")
        else:
            print("❌ Failed to load original data")
    except Exception as e:
        print(f"❌ Error loading original data: {e}")
    
    print()
    
    # Test 2: Check current feedback data
    print("2. Testing feedback data retrieval...")
    try:
        feedback_df = retrainer.get_feedback_data(days_back=30)
        print(f"✅ Retrieved {len(feedback_df)} feedback entries")
        if not feedback_df.empty:
            print(f"   Vote distribution: {feedback_df['vote'].value_counts().to_dict()}")
            disagreements = feedback_df[feedback_df['vote'] == 'disagree']
            print(f"   Disagreements: {len(disagreements)}")
        else:
            print("   No feedback data found")
    except Exception as e:
        print(f"❌ Error retrieving feedback: {e}")
    
    print()
    
    # Test 3: Test mixed training data preparation
    print("3. Testing mixed training data preparation...")
    try:
        if not feedback_df.empty:
            X_mixed, y_mixed, weights_mixed = retrainer.prepare_training_data(feedback_df)
            if X_mixed is not None:
                print(f"✅ Successfully prepared mixed training data")
                print(f"   Total samples: {len(X_mixed)}")
                print(f"   Features shape: {X_mixed.shape}")
                print(f"   Labels distribution: {np.bincount(y_mixed.astype(int))}")
                print(f"   Weight range: {weights_mixed.min():.2f} - {weights_mixed.max():.2f}")
                
                # Check for feedback vs original data weights
                high_weight_count = np.sum(weights_mixed > 0.5)
                low_weight_count = np.sum(weights_mixed <= 0.5)
                print(f"   High weight samples (feedback): {high_weight_count}")
                print(f"   Low weight samples (original): {low_weight_count}")
            else:
                print("❌ Failed to prepare mixed training data")
        else:
            print("⚠️  No feedback data to test with")
    except Exception as e:
        print(f"❌ Error preparing mixed data: {e}")
    
    print()
    
    # Test 4: Check retraining criteria
    print("4. Testing retraining criteria...")
    try:
        should_retrain, reason = retrainer.should_retrain()
        print(f"Should retrain: {should_retrain}")
        print(f"Reason: {reason}")
        
        # Show current thresholds
        print(f"Current thresholds:")
        print(f"   Min feedback: {retrainer.min_feedback_threshold}")
        print(f"   Disagreement rate: {retrainer.disagreement_threshold * 100}%")
    except Exception as e:
        print(f"❌ Error checking retraining criteria: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_mixed_training()
