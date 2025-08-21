from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pickle
import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fittrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm
    current_weight = db.Column(db.Float, nullable=False)  # in kg
    fitness_goal = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.String(50), nullable=False)  # strength, fat_loss, endurance, muscle_growth
    description = db.Column(db.Text)
    weekly_plan = db.Column(db.JSON)  # JSON structure for weekly workout plan

class UserWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('workout_template.id'), nullable=False)
    custom_plan = db.Column(db.JSON)  # JSON structure for customized plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories_per_100g = db.Column(db.Float, nullable=False)
    protein_per_100g = db.Column(db.Float, nullable=False)
    carbs_per_100g = db.Column(db.Float, default=0)
    fat_per_100g = db.Column(db.Float, default=0)

class NutritionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity_grams = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)
    meal_type = db.Column(db.String(20), default='other')  # breakfast, lunch, dinner, snack, other

class ProgressLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_fat_percentage = db.Column(db.Float)
    notes = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)

# Load ML Model
def load_prediction_model():
    try:
        # You'll need to place your .pkl model in the models folder
        model_path = os.path.join('models', 'weight_prediction_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        else:
            print("Model file not found. Please place your .pkl model in the models folder.")
            return None
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

prediction_model = load_prediction_model()

# Helper functions
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            name=data['name'],
            age=int(data['age']),
            gender=data['gender'],
            height=float(data['height']),
            current_weight=float(data['current_weight']),
            fitness_goal=data['fitness_goal']
        )
        
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            else:
                return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
            if request.is_json:
                return jsonify({'error': error}), 401
            else:
                flash(error)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get recent progress
    recent_progress = ProgressLog.query.filter_by(user_id=user.id).order_by(ProgressLog.date.desc()).limit(5).all()
    
    # Get today's nutrition
    today_nutrition = db.session.query(NutritionLog, FoodItem).join(FoodItem).filter(
        NutritionLog.user_id == user.id,
        NutritionLog.date == date.today()
    ).all()
    
    total_calories = sum([
        (log.quantity_grams / 100) * food.calories_per_100g 
        for log, food in today_nutrition
    ])
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_progress=recent_progress,
                         total_calories=round(total_calories, 1))

@app.route('/workout-planner')
@login_required
def workout_planner():
    templates = WorkoutTemplate.query.all()
    user_workouts = UserWorkout.query.filter_by(user_id=session['user_id'], is_active=True).all()
    return render_template('workout_planner.html', templates=templates, user_workouts=user_workouts)

@app.route('/nutrition-tracker')
@login_required
def nutrition_tracker():
    food_items = FoodItem.query.all()
    
    # Get today's logs
    today_logs = db.session.query(NutritionLog, FoodItem).join(FoodItem).filter(
        NutritionLog.user_id == session['user_id'],
        NutritionLog.date == date.today()
    ).all()
    
    return render_template('nutrition_tracker.html', food_items=food_items, today_logs=today_logs)

@app.route('/progress-tracker')
@login_required
def progress_tracker():
    progress_logs = ProgressLog.query.filter_by(user_id=session['user_id']).order_by(ProgressLog.date.desc()).all()
    return render_template('progress_tracker.html', progress_logs=progress_logs)

@app.route('/prediction-tool')
@login_required
def prediction_tool():
    user = User.query.get(session['user_id'])
    return render_template('prediction_tool.html', user=user)

# API Routes
@app.route('/api/workout/select-template', methods=['POST'])
@login_required
def select_workout_template():
    data = request.json
    template_id = data.get('template_id')
    
    # Deactivate previous workouts
    UserWorkout.query.filter_by(user_id=session['user_id'], is_active=True).update({'is_active': False})
    
    # Create new active workout
    user_workout = UserWorkout(
        user_id=session['user_id'],
        template_id=template_id,
        custom_plan=data.get('custom_plan'),
        is_active=True
    )
    
    db.session.add(user_workout)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/nutrition/log', methods=['POST'])
@login_required
def log_nutrition():
    data = request.json
    
    nutrition_log = NutritionLog(
        user_id=session['user_id'],
        food_id=data['food_id'],
        quantity_grams=data['quantity_grams'],
        meal_type=data.get('meal_type', 'other')
    )
    
    db.session.add(nutrition_log)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/progress/log', methods=['POST'])
@login_required
def log_progress():
    data = request.json
    
    progress_log = ProgressLog(
        user_id=session['user_id'],
        weight=data['weight'],
        body_fat_percentage=data.get('body_fat_percentage'),
        notes=data.get('notes', '')
    )
    
    db.session.add(progress_log)
    
    # Update user's current weight
    user = User.query.get(session['user_id'])
    user.current_weight = data['weight']
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/progress/data')
@login_required
def get_progress_data():
    progress_logs = ProgressLog.query.filter_by(user_id=session['user_id']).order_by(ProgressLog.date).all()
    
    data = {
        'dates': [log.date.strftime('%Y-%m-%d') for log in progress_logs],
        'weights': [log.weight for log in progress_logs],
        'body_fat': [log.body_fat_percentage for log in progress_logs if log.body_fat_percentage]
    }
    
    return jsonify(data)

@app.route('/api/predict-weight', methods=['POST'])
@login_required
def predict_weight():
    print(f"[DEBUG] Prediction request received from user {session.get('user_id')}")
    
    if not prediction_model:
        print("[ERROR] Prediction model not available")
        return jsonify({'error': 'Prediction model not available'}), 500
    
    # Check if request has JSON data
    if not request.is_json:
        print("[ERROR] Request is not JSON")
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.json
    print(f"[DEBUG] Received data: {data}")
    
    # Validate required fields
    required_fields = ['current_weight', 'daily_calories', 'weekly_workout_minutes', 'weeks_ahead']
    missing_fields = [field for field in required_fields if field not in data or data[field] == '']
    
    if missing_fields:
        print(f"[ERROR] Missing required fields: {missing_fields}")
        return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
    
    try:
        # Convert and validate input data
        current_weight = float(data['current_weight'])
        daily_calories = float(data['daily_calories'])
        weekly_workout_minutes = float(data['weekly_workout_minutes'])
        weeks_ahead = int(data['weeks_ahead'])
        
        print(f"[DEBUG] Parsed values: weight={current_weight}, calories={daily_calories}, workout={weekly_workout_minutes}, weeks={weeks_ahead}")
        
        # Validate ranges
        if not (20 <= current_weight <= 300):
            return jsonify({'error': 'Current weight must be between 20 and 300 kg'}), 400
        if not (800 <= daily_calories <= 5000):
            return jsonify({'error': 'Daily calories must be between 800 and 5000'}), 400
        if not (0 <= weekly_workout_minutes <= 2000):
            return jsonify({'error': 'Weekly workout minutes must be between 0 and 2000'}), 400
        if not (1 <= weeks_ahead <= 52):
            return jsonify({'error': 'Weeks ahead must be between 1 and 52'}), 400
        
        # Prepare input data as DataFrame with exact feature names the model expects
        input_data = pd.DataFrame({
            'current_weight': [current_weight],
            'daily_calories': [daily_calories],
            'weekly_workout_minutes': [weekly_workout_minutes],
            'weeks_ahead': [weeks_ahead]
        })
        
        print(f"[DEBUG] Input DataFrame shape: {input_data.shape}")
        print(f"[DEBUG] Input DataFrame columns: {list(input_data.columns)}")
        print(f"[DEBUG] Input DataFrame:\n{input_data}")
        
        # Make prediction using DataFrame with proper column names
        prediction = prediction_model.predict(input_data)
        predicted_weight = prediction[0]
        
        print(f"[DEBUG] Raw prediction: {predicted_weight}")
        
        # Ensure realistic bounds (weight shouldn't go below 30 or above 300)
        predicted_weight = max(30.0, min(300.0, predicted_weight))
        weight_change = predicted_weight - current_weight
        
        result = {
            'predicted_weight': round(predicted_weight, 2),
            'weight_change': round(weight_change, 2)
        }
        
        print(f"[DEBUG] Final result: {result}")
        
        return jsonify(result)
    
    except ValueError as e:
        error_msg = f'Invalid input data: {str(e)}'
        print(f"[ERROR] {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    except Exception as e:
        error_msg = f'Prediction error: {str(e)}'
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/nutrition/summary')
@login_required
def get_nutrition_summary():
    today_logs = db.session.query(NutritionLog, FoodItem).join(FoodItem).filter(
        NutritionLog.user_id == session['user_id'],
        NutritionLog.date == date.today()
    ).all()
    
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for log, food in today_logs:
        multiplier = log.quantity_grams / 100
        total_calories += food.calories_per_100g * multiplier
        total_protein += food.protein_per_100g * multiplier
        total_carbs += food.carbs_per_100g * multiplier
        total_fat += food.fat_per_100g * multiplier
    
    return jsonify({
        'total_calories': round(total_calories, 1),
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fat': round(total_fat, 1)
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
