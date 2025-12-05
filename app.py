from flask import Flask, render_template, jsonify, request
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert timestamp to readable datetime"""
    if not timestamp:
        return "Never"
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp)   

# Backend API URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

# ========== CONTEXT PROCESSOR ==========
@app.context_processor
def inject_backend_url():
    return dict(backend_url=BACKEND_URL)

# ========== TEMPLATE FILTERS ==========
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert timestamp to readable datetime"""
    if not timestamp:
        return "Never"
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp)

# ========== ROUTES ==========
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard with system overview"""
    try:
        print(f"🔄 Fetching dashboard data from {BACKEND_URL}")
        
        # Get system status from backend
        status_response = requests.get(f'{BACKEND_URL}/api/status', timeout=5)
        print(f"Status API Response: {status_response.status_code}")
        
        sensors_response = requests.get(f'{BACKEND_URL}/api/sensors', timeout=5)
        print(f"Sensors API Response: {sensors_response.status_code}")
        
        users_response = requests.get(f'{BACKEND_URL}/api/users', timeout=5)
        print(f"Users API Response: {users_response.status_code}")
        
        # Parse responses
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Status Data: {status_data}")
        else:
            status_data = {'success': False, 'error': f'Status API returned {status_response.status_code}'}
            print(f"Status API Error: {status_response.text}")
        
        if sensors_response.status_code == 200:
            sensors_data = sensors_response.json()
            print(f"Sensors Data Keys: {sensors_data.keys() if isinstance(sensors_data, dict) else 'Not dict'}")
            sensors_dict = sensors_data.get('sensors', {})
            print(f"Number of sensors: {len(sensors_dict)}")
        else:
            sensors_dict = {}
            print(f"Sensors API Error: {sensors_response.text}")
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            print(f"Users Data: {users_data.get('count', 0)} users")
            users_count = users_data.get('count', 0)
        else:
            users_count = 0
            print(f"Users API Error: {users_response.text}")
        
        # Jika semua API gagal, coba tes koneksi backend
        if not sensors_dict and not users_count:
            print("⚠️ No data received, testing backend connection...")
            test_response = requests.get(f'{BACKEND_URL}/api/health', timeout=2)
            if test_response.status_code != 200:
                return render_template('dashboard.html', 
                                     error=f'Backend API tidak terhubung. Pastikan backend berjalan di {BACKEND_URL}')
        
        return render_template('dashboard.html',
                             status=status_data,
                             sensors=sensors_dict,
                             users_count=users_count)
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Tidak dapat terhubung ke backend di {BACKEND_URL}. Pastikan backend sedang berjalan."
        print(f"Connection Error: {error_msg}")
        return render_template('dashboard.html', error=error_msg)
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout saat menghubungi backend. Backend mungkin lambat atau tidak responsif."
        print(f"Timeout Error: {error_msg}")
        return render_template('dashboard.html', error=error_msg)
    except Exception as e:
        error_msg = f"Error tidak terduga: {str(e)}"
        print(f"Unexpected Error: {error_msg}")
        return render_template('dashboard.html', error=error_msg)

@app.route('/sensors')
def sensors():
    """Display all sensors"""
    try:
        print(f"🔄 Fetching sensors from {BACKEND_URL}/api/sensors")
        response = requests.get(f'{BACKEND_URL}/api/sensors', timeout=5)
        print(f"Sensors response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            sensors_dict = data.get('sensors', {})
            
            # Hitung statistics
            total_sensors = len(sensors_dict)
            active_sensors = sum(1 for s in sensors_dict.values() if s.get('status') == 'active')
            temperature_sensors = sum(1 for s in sensors_dict.values() if s.get('type') == 'temperature')
            ph_sensors = sum(1 for s in sensors_dict.values() if s.get('type') == 'ph')
            humidity_sensors = sum(1 for s in sensors_dict.values() if s.get('type') == 'humidity')
            
            print(f"Stats: Total={total_sensors}, Active={active_sensors}")
            
            return render_template('sensors.html', 
                                 sensors=sensors_dict,
                                 total_sensors=total_sensors,
                                 active_sensors=active_sensors,
                                 temperature_sensors=temperature_sensors,
                                 ph_sensors=ph_sensors,
                                 humidity_sensors=humidity_sensors)
        else:
            error_msg = f"Failed to fetch sensors: {response.status_code}"
            return render_template('sensors.html', 
                                 error=error_msg, 
                                 sensors={},
                                 total_sensors=0,
                                 active_sensors=0,
                                 temperature_sensors=0,
                                 ph_sensors=0,
                                 humidity_sensors=0)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return render_template('sensors.html', 
                             error=error_msg, 
                             sensors={},
                             total_sensors=0,
                             active_sensors=0,
                             temperature_sensors=0,
                             ph_sensors=0,
                             humidity_sensors=0)

@app.route('/users')
def users():
    """Display all users"""
    try:
        print(f"🔄 Fetching users from {BACKEND_URL}/api/users")
        
        # Test connection first
        test_response = requests.get(f'{BACKEND_URL}/api/health', timeout=2)
        if test_response.status_code != 200:
            print("⚠️ Backend not reachable")
            return render_template('users.html', 
                                 error=f"Backend not reachable at {BACKEND_URL}",
                                 users={})
        
        # Get users data
        response = requests.get(f'{BACKEND_URL}/api/users', timeout=5)
        print(f"Users API Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Raw data received: {data}")
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'users' in data:
                    users_dict = data['users']
                    print(f"Found users in 'users' key: {len(users_dict)} users")
                else:
                    # Maybe data is already the users dict
                    users_dict = data
                    print(f"Using data directly as users dict: {len(users_dict)} items")
            else:
                users_dict = {}
                print("Data is not a dictionary")
                
            print(f"Users to template: {users_dict}")
            return render_template('users.html', users=users_dict)
            
        else:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            print(error_msg)
            return render_template('users.html', 
                                 error=error_msg, 
                                 users={})
            
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Cannot connect to backend at {BACKEND_URL}"
        print(f"❌ {error_msg}")
        return render_template('users.html', 
                             error=error_msg, 
                             users={})
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return render_template('users.html', 
                             error=error_msg, 
                             users={})
    
@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/proxy/<path:endpoint>', methods=['GET'])
def proxy_get(endpoint):
    """Proxy GET requests to backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/{endpoint}')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Frontend health check"""
    backend_ok = check_backend_connection()
    return jsonify({
        'status': 'healthy',
        'service': 'frontend',
        'backend_connected': backend_ok,
        'backend_url': BACKEND_URL
    })

def check_backend_connection():
    """Check if backend is accessible"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/health', timeout=2)
        return response.status_code == 200
    except:
        return False

@app.route('/test-backend')
def test_backend():
    """Test page to check backend connection"""
    try:
        # Test multiple endpoints
        endpoints = {
            'health': f'{BACKEND_URL}/api/health',
            'status': f'{BACKEND_URL}/api/status',
            'sensors': f'{BACKEND_URL}/api/sensors',
            'users': f'{BACKEND_URL}/api/users'
        }
        
        results = {}
        for name, url in endpoints.items():
            try:
                response = requests.get(url, timeout=3)
                results[name] = {
                    'status': response.status_code,
                    'success': response.status_code == 200,
                    'url': url
                }
                if response.status_code == 200:
                    results[name]['data'] = response.json()
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'success': False,
                    'error': str(e),
                    'url': url
                }
        
        return render_template('test_backend.html', 
                             results=results, 
                             backend_url=BACKEND_URL)
    except Exception as e:
        return f"Error testing backend: {str(e)}"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    print(f"🚀 Starting Frontend on port {port}...")
    print(f"🌐 Access: http://localhost:{port}")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"🔍 Backend Health: {'✅ OK' if check_backend_connection() else '❌ Not connected'}")
    app.run(debug=True, port=port, host='0.0.0.0')