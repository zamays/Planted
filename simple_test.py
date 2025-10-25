#!/usr/bin/env python3
"""
Simple Flask test to diagnose blank screen issues
"""

from flask import Flask, render_template_string
import webbrowser
import threading
import time

app = Flask(__name__)

# Simple inline HTML template to test basic Flask functionality
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Garden Manager Test</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: #f0f8f0;
            color: #333;
        }
        .header { 
            background: #4A7C59; 
            color: white; 
            padding: 20px; 
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .btn { 
            background: #4A7C59; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px;
            display: inline-block;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 Garden Manager - Test Page</h1>
        <p>If you can see this, Flask is working!</p>
    </div>
    
    <div class="card">
        <h2>✅ Flask Status: WORKING</h2>
        <p>This confirms that:</p>
        <ul>
            <li>Python Flask server is running</li>
            <li>HTML templates are rendering</li>
            <li>CSS styles are loading</li>
            <li>Browser can display the content</li>
        </ul>
    </div>
    
    <div class="card">
        <h2>🔧 Next Steps</h2>
        <p>Now let's test the main application:</p>
        <a href="/main" class="btn">🚀 Test Main App</a>
        <a href="/basic" class="btn">📋 Basic Dashboard</a>
    </div>
    
    <div class="card">
        <h2>🌐 Debug Info</h2>
        <p><strong>URL:</strong> http://localhost:5000</p>
        <p><strong>Time:</strong> {{ current_time }}</p>
        <p><strong>Status:</strong> Server is responsive</p>
    </div>
</body>
</html>
"""

BASIC_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Basic Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #F5F5DC; }
        .header { background: linear-gradient(135deg, #4A7C59, #2E5233); color: white; padding: 20px; border-radius: 10px; }
        .nav { background: white; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .nav a { margin-right: 20px; text-decoration: none; color: #4A7C59; font-weight: bold; }
        .card { background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 Garden Manager</h1>
        <p>📍 New York, NY • 🍃 Summer Season</p>
    </div>
    
    <div class="nav">
        <a href="/">🏠 Dashboard</a>
        <a href="/plants">🌿 Browse Plants</a>
        <a href="/garden">🗂️ Garden Layout</a>
        <a href="/care">📅 Care Schedule</a>
        <a href="/weather">🌦️ Weather</a>
    </div>
    
    <div class="card">
        <h2>Garden Dashboard</h2>
        <p>🌱 Welcome to Garden Manager!</p>
        <p>This is a simplified version to test the interface.</p>
    </div>
    
    <div class="card">
        <h3>Quick Stats</h3>
        <p>🗂️ Garden Plots: 0</p>
        <p>🌱 Active Plants: 0</p>
        <p>📋 Tasks Due: 0</p>
    </div>
</body>
</html>
"""

@app.route('/')
def test_page():
    """Simple test page to verify Flask is working"""
    import datetime
    return render_template_string(SIMPLE_HTML, current_time=datetime.datetime.now())

@app.route('/basic')
def basic_dashboard():
    """Basic dashboard without complex dependencies"""
    return render_template_string(BASIC_DASHBOARD)

@app.route('/main')
def main_app():
    """Try to load the actual main app"""
    try:
        # Import the main app components
        import sys
        import os
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from garden_manager.database.plant_data import PlantDatabase
        
        # Test database initialization
        plant_db = PlantDatabase()
        plants = plant_db.get_plants_by_season('spring')
        
        return f"""
        <html>
        <head><title>Main App Test</title></head>
        <body style="font-family: Arial; margin: 40px; background: #f0f8f0;">
            <h1>🌱 Main App Status</h1>
            <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h2>✅ Success!</h2>
                <p>Plant database loaded successfully</p>
                <p>Found {len(plants)} spring plants</p>
                <p><a href="/" style="background: #4A7C59; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">← Back to Test</a></p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Main App Error</title></head>
        <body style="font-family: Arial; margin: 40px; background: #f8d7da;">
            <h1>❌ Main App Error</h1>
            <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h2>Error Details:</h2>
                <p><strong>Error:</strong> {str(e)}</p>
                <p><strong>Type:</strong> {type(e).__name__}</p>
                <p><a href="/" style="background: #4A7C59; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">← Back to Test</a></p>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    print("🧪 Starting Simple Flask Test...")
    print("   📍 URL: http://localhost:5000")
    print("   🎯 Purpose: Diagnose blank screen issues")
    
    def open_browser():
        time.sleep(1)
        try:
            webbrowser.open('http://localhost:5000')
            print("   ✅ Browser opened")
        except:
            print("   ⚠️ Could not open browser - please visit http://localhost:5000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=True, host='localhost', port=5000, use_reloader=False)