from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)

# PostgreSQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/rspns'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

HOST_IP = "192.168.108.217"
db = SQLAlchemy(app)
socketio = SocketIO(app)

# --- Load your pre-trained sklearn model and scaler ---
# IMPORTANT: Replace 'path/to/model_rf.pkl' and 'path/to/scaler.pkl'
# with the actual paths to your saved model and scaler files.
model = joblib.load('model_rf.pkl')
scaler = joblib.load('scaler.pkl')
print("Sklearn model and scaler loaded successfully!")


# Define the features your model was trained on, IN THE CORRECT ORDER
MODEL_FEATURES = ['temperatur', 'kelembaban', 'kadar_co2', 'kebocoran_gas', 'intensitas_cahaya', 'energy_consumption']


def timestamp():
    now = datetime.now()
    return f"{now.day} - {now.month} - {now.year} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"

# Define the SensorData model
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.BigInteger, primary_key=True)
    temp = db.Column(db.Numeric(6, 3))
    humidity = db.Column(db.Numeric(5, 2))
    illuminance = db.Column(db.REAL)
    co2 = db.Column(db.Integer)
    noise = db.Column(db.Numeric(5, 2))
    current = db.Column(db.Numeric(7, 4))
    voltage = db.Column(db.Numeric(7, 4))
    gas_detection = db.Column(db.Boolean)
    earthquake = db.Column(db.Boolean)
    time = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

# Define the PeopleCount model (for comfort prediction)
class PeopleCount(db.Model):
    __tablename__ = 'people_count'
    id = db.Column(db.BigInteger, primary_key=True)
    # This column will store boolean comfort prediction
    jumlah_orang = db.Column(db.Boolean)
    time = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

@app.route('/', methods=['GET'])
def get_sensor_data():
    sensors = SensorData.query.all()
    people_counts = PeopleCount.query.all()
    return render_template('index.html', sensors=sensors, people_counts=people_counts)

# Route to get all sensor data
@app.route('/api/', methods=['GET'])
def api_get_sensor_data():
    sensors = SensorData.query.all()
    sensor_list = [{
        "id": sensor.id,
        "temp": float(sensor.temp) if sensor.temp else None,
        "humidity": float(sensor.humidity) if sensor.humidity else None,
        "illuminance": float(sensor.illuminance) if sensor.illuminance else None,
        "co2": sensor.co2,
        "noise": float(sensor.noise) if sensor.noise else None,
        "current": float(sensor.current) if sensor.current else None,
        "voltage": float(sensor.voltage) if sensor.voltage else None,
        "gas_detection": sensor.gas_detection,
        "earthquake": sensor.earthquake,
        "time": sensor.time.isoformat() if sensor.time else None,
    } for sensor in sensors]
    
    people_counts = PeopleCount.query.all()
    people_list = [{
        "id": count.id,
        "jumlah_orang": count.jumlah_orang,
        "time": count.time.isoformat() if count.time else None
    } for count in people_counts]
    
    return jsonify({"sensor_data": sensor_list, "people_counts": people_list})

# --- New Helper Function for Comfort Prediction ---
def predict_and_store_comfort(sensor_data: dict):
    """
    Predicts comfort based on sensor data and stores it in the database.
    Returns a dictionary with prediction details or an error message.
    """
    try:
        # Map sensor data keys to model feature keys if they differ
        # For example, if sensor_data has 'temp' but model expects 'temperatur'
        # You'll need to create this mapping or ensure your sensor data keys match MODEL_FEATURES
        # For simplicity, assuming sensor_data keys directly match MODEL_FEATURES for now.
        
        # Validate that all required model features are present in the provided sensor_data
        for feature in MODEL_FEATURES:
            if feature not in sensor_data:
                # This indicates an issue with the sensor data format or missing data
                print(f"Warning: Missing model feature '{feature}' in sensor data for comfort prediction.")
                return {"error": f"Missing model feature: {feature}"}

        # Create a Pandas DataFrame from the incoming data, ensuring correct feature order
        input_df = pd.DataFrame([[sensor_data.get(f) for f in MODEL_FEATURES]], columns=MODEL_FEATURES)

        # Preprocess the input using the loaded scaler
        input_scaled = scaler.transform(input_df)

        # Make prediction using the loaded sklearn model
        prediction_raw = model.predict(input_scaled)[0]
        
        # Convert prediction to boolean: True for 'nyaman' (0), False for 'tidak nyaman' (1)
        predicted_comfort = bool(prediction_raw == 0)

        prob = model.predict_proba(input_scaled)[0].tolist()
        comfort_prob = prob[0]
        discomfort_prob = prob[1]

        new_comfort_entry = PeopleCount(
            jumlah_orang=predicted_comfort
        )

        db.session.add(new_comfort_entry)
        db.session.commit()
        
        # Emit updated data to WebSocket clients
        send_people_count()

        return {
            "predicted_comfort": "nyaman" if predicted_comfort else "tidak nyaman",
            "probabilities": {
                "nyaman": comfort_prob,
                "tidak_nyaman": discomfort_prob
            }
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error during comfort prediction: {str(e)}"}


# Route to add new sensor data (POST)
@app.route('/api/send', methods=['POST'])
def add_sensor_data():
    data = request.get_json()
    
    required_fields = [
        'temp', 'humidity', 'illuminance', 'co2', 'noise',
        'current', 'voltage', 'gas_detection', 'earthquake'
    ]
    
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing fields in sensor data"}), 400

    new_sensor = SensorData(
        temp=data['temp'],
        humidity=data['humidity'],
        illuminance=data['illuminance'],
        co2=data['co2'],
        noise=data['noise'],
        current=data['current'],
        voltage=data['voltage'],
        gas_detection=data['gas_detection'],
        earthquake=data['earthquake']
    )

    try:
        db.session.add(new_sensor)
        db.session.commit()
        send_sensor_data() # Emit latest sensor data

        # --- Call the comfort prediction helper function here ---
        # Ensure 'data' contains the keys expected by MODEL_FEATURES
        # You might need to adjust 'data' keys to match your MODEL_FEATURES
        # E.g., if sensor data has 'temp' but MODEL_FEATURES expects 'temperatur',
        # you'd do: comfort_input = {'temperatur': data['temp'], ...}
        
        # For simplicity, assuming current 'data' directly contains model features or can be easily mapped
        comfort_prediction_result = predict_and_store_comfort({
            'temperatur': data.get('temp'), # Map 'temp' from sensor data to 'temperatur' for model
            'kelembaban': data.get('humidity'), # Map 'humidity' to 'kelembaban'
            'kadar_co2': data.get('co2'), # Map 'co2' to 'kadar_co2'
            'kebocoran_gas': data.get('gas_detection'), # Map 'gas_detection' to 'kebocoran_gas'
            'intensitas_cahaya': data.get('illuminance'), # Map 'illuminance' to 'intensitas_cahaya'
            'energy_consumption': data.get('current') * data.get('voltage', 0) # Example: Calculate energy from current and voltage
        })


        if "error" in comfort_prediction_result:
            # Handle prediction error without failing the sensor data storage
            print(f"Comfort prediction encountered an error: {comfort_prediction_result['error']}")
            # You might choose to return this error or just log it
            return jsonify({"message": "Sensor data added successfully, but comfort prediction failed", 
                            "comfort_prediction_error": comfort_prediction_result['error']}), 201
        
        return jsonify({"message": "Sensor data and comfort prediction added successfully",
                        "comfort_prediction": comfort_prediction_result['predicted_comfort'],
                        "comfort_probabilities": comfort_prediction_result['probabilities']}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to add comfort data directly (optional, if you still want this endpoint)
@app.route('/api/people', methods=['POST'])
def add_comfort_prediction_direct():
    # This endpoint can still exist if you want to trigger comfort prediction
    # directly with just comfort-related features, without storing sensor data first.
    # It would call predict_and_store_comfort similarly to add_sensor_data.
    
    data = request.get_json()
    if not all(feature in data for feature in MODEL_FEATURES):
        missing_features = [f for f in MODEL_FEATURES if f not in data]
        return jsonify({"error": f"Missing one or more required model features: {missing_features}"}), 400

    comfort_prediction_result = predict_and_store_comfort(data)

    if "error" in comfort_prediction_result:
        return jsonify({"error": comfort_prediction_result['error']}), 500
    
    return jsonify({
        "message": "Comfort prediction added successfully",
        "predicted_comfort": comfort_prediction_result['predicted_comfort'],
        "probabilities": comfort_prediction_result['probabilities']
    }), 201


def send_sensor_data():
    latest_sensor = SensorData.query.order_by(SensorData.time.desc()).first()
    
    sensor_list = []
    if latest_sensor:
        sensor_list.append({
            "id": latest_sensor.id,
            "temp": float(latest_sensor.temp) if latest_sensor.temp else None,
            "humidity": float(latest_sensor.humidity) if latest_sensor.humidity else None,
            "illuminance": float(latest_sensor.illuminance) if latest_sensor.illuminance else None,
            "co2": latest_sensor.co2,
            "noise": float(latest_sensor.noise) if latest_sensor.noise else None,
            "current": float(latest_sensor.current) if latest_sensor.current else None,
            "voltage": float(latest_sensor.voltage) if latest_sensor.voltage else None,
            "gas_detection": latest_sensor.gas_detection,
            "earthquake": latest_sensor.earthquake,
            "time": latest_sensor.time.isoformat() if latest_sensor.time else None,
            "timestamp": timestamp()
        })
    socketio.emit('sensor_data', sensor_list)

def send_people_count():
    latest_count = PeopleCount.query.order_by(PeopleCount.time.desc()).first()
    
    count_data = []
    if latest_count:
        count_data.append({
            "id": latest_count.id,
            "jumlah_orang": latest_count.jumlah_orang, # This will be the boolean comfort (True/False)
            "time": latest_count.time.isoformat() if latest_count.time else None,
            "timestamp": timestamp()
        })
    socketio.emit('people_count', count_data)

# WebSocket connection handlers
@socketio.on('connect')
def handle_connect():
    send_sensor_data()
    send_people_count()

if __name__ == '__main__':
    # You might need to uncomment and run this once if you change the database schema
    # (e.g., from BigInteger to Boolean for jumlah_orang)
    # with app.app_context():
    #     db.create_all()
    socketio.run(app, host=HOST_IP, debug=True, port=5000)