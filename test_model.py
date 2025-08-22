#!/usr/bin/env python3
"""
Test script to verify the actual ML model and understand its input format
"""

import pickle
import numpy as np
import pandas as pd

def test_model():
    """Test the actual ML model to understand its requirements"""
    
    try:
        # Load the actual model
        with open('models/weight_prediction_model.pkl', 'rb') as f:
            model = pickle.load(f)
        
        print(" Model loaded successfully!")
        print(f"Model type: {type(model)}")
        
        # Check if model has common attributes
        if hasattr(model, 'feature_names_in_'):
            print(f"Model features: {model.feature_names_in_}")
        
        if hasattr(model, 'n_features_in_'):
            print(f"Number of features expected: {model.n_features_in_}")
        
        if hasattr(model, 'coef_'):
            print(f"Model coefficients shape: {model.coef_.shape}")
        
        # Test with different input formats to see what works
        print("\n=== Testing different input formats ===")
        
        # Test 1: Simple array with 4 features (our expected format)
        try:
            test_input_1 = np.array([[75.0, 2000.0, 300.0, 8.0]])  # weight, calories, workout_min, weeks
            prediction_1 = model.predict(test_input_1)
            print(f"✅ Test 1 (4 features) - Success: {prediction_1}")
        except Exception as e:
            print(f"❌ Test 1 (4 features) - Failed: {e}")
        
        # Test 2: Different number of features
        for n_features in [1, 2, 3, 5, 6, 7, 8]:
            try:
                test_input = np.random.rand(1, n_features) * 100  # Random values
                prediction = model.predict(test_input)
                print(f"✅ Test with {n_features} features - Success: {prediction[0]:.2f}")
                break  # If this works, we found the right number
            except Exception as e:
                print(f"❌ Test with {n_features} features - Failed: {str(e)[:50]}...")
        
        # Test 3: Try with pandas DataFrame
        try:
            df_input = pd.DataFrame({
                'current_weight': [75.0],
                'daily_calories': [2000.0],
                'weekly_workout_minutes': [300.0],
                'weeks_ahead': [8.0]
            })
            prediction_df = model.predict(df_input)
            print(f"✅ DataFrame test - Success: {prediction_df}")
        except Exception as e:
            print(f"❌ DataFrame test - Failed: {e}")
        
        # Test 4: Try common ML features
        common_features = [
            ['weight', 'height', 'age', 'gender', 'calories', 'exercise'],
            ['weight', 'calories', 'exercise', 'weeks'],
            ['weight', 'calories', 'exercise'],
            ['weight', 'bmi', 'calories', 'exercise', 'weeks'],
            ['age', 'gender', 'weight', 'height', 'calories', 'exercise', 'weeks'],
        ]
        
        for i, feature_set in enumerate(common_features):
            try:
                # Create sample data matching feature count
                n_features = len(feature_set)
                if n_features == 3:
                    sample_data = [[75.0, 2000.0, 300.0]]
                elif n_features == 4:
                    sample_data = [[75.0, 2000.0, 300.0, 8.0]]
                elif n_features == 5:
                    sample_data = [[75.0, 25.0, 2000.0, 300.0, 8.0]]  # Added BMI
                elif n_features == 6:
                    sample_data = [[75.0, 2000.0, 300.0, 8.0, 25.0, 1.0]]  # Added BMI and gender
                elif n_features == 7:
                    sample_data = [[30.0, 1.0, 75.0, 175.0, 2000.0, 300.0, 8.0]]  # Age, gender, weight, height, calories, exercise, weeks
                else:
                    continue
                
                test_array = np.array(sample_data)
                prediction = model.predict(test_array)
                print(f"✅ Feature set {i+1} ({feature_set}) - Success: {prediction[0]:.2f}")
                print(f"   Sample input shape: {test_array.shape}")
                break
            except Exception as e:
                print(f"❌ Feature set {i+1} ({feature_set}) - Failed: {str(e)[:50]}...")
        
        # If we have a working prediction, test edge cases
        print(f"\n=== Testing edge cases ===")
        try:
            # Test extreme values
            extreme_tests = [
                [50.0, 1200.0, 0.0, 12.0],    # Low weight, low calories, no exercise
                [100.0, 3000.0, 600.0, 4.0],   # High weight, high calories, lots of exercise
                [70.0, 2000.0, 150.0, 1.0],    # Normal values, short timeframe
                [80.0, 1800.0, 300.0, 24.0],   # Normal values, long timeframe
            ]
            
            for i, test_case in enumerate(extreme_tests):
                try:
                    prediction = model.predict([test_case])
                    weight_change = prediction[0] - test_case[0]
                    print(f"Test {i+1}: Input {test_case} → Prediction: {prediction[0]:.1f}kg (Change: {weight_change:+.1f}kg)")
                except Exception as e:
                    print(f"Extreme test {i+1} failed: {e}")
        except:
            print("Could not run edge case tests")
            
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("Testing the actual ML model...")
    success = test_model()
    if success:
        print("\n🎉 Model testing completed! Check the successful format above.")
    else:
        print("\n❌ Model testing failed. Please check the model file.")
