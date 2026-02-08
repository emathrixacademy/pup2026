"""
Seed ES (Embedded Systems) Activities for Sessions 1-12
Each session has one main activity worth 100 points
Using HTML formatting for proper display
"""

import sqlite3

def seed_es_activities():
    conn = sqlite3.connect('classroom_lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get ES subject ID
    cursor.execute("SELECT id FROM subjects WHERE code = 'ES'")
    result = cursor.fetchone()
    if not result:
        print("ES subject not found. Please create the subject first.")
        return

    subject_id = result['id']

    # ES Activities for Sessions 1-12 with HTML formatting
    activities_data = {
        1: {
            "title": "Activity 1: Board Identification and IDE Setup",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Identify components on an Arduino/ESP32 board</li>
    <li>Successfully install and configure Arduino IDE</li>
    <li>Upload first program</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>Arduino Uno or ESP32 board</li>
    <li>USB cable</li>
    <li>Computer with internet</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Label 10 components on the board diagram</td><td>20</td></tr>
    <tr><td>2</td><td>Install Arduino IDE and configure board</td><td>20</td></tr>
    <tr><td>3</td><td>Install ESP32 board support (if using ESP32)</td><td>15</td></tr>
    <tr><td>4</td><td>Successfully upload Blink program</td><td>25</td></tr>
    <tr><td>5</td><td>Modify blink timing (500ms on, 200ms off)</td><td>20</td></tr>
</table>

<h4>Deliverables:</h4>
<ol>
    <li>Labeled board diagram (photo/drawing)</li>
    <li>Screenshot of successful upload</li>
    <li>Video of modified blink pattern (5-10 seconds)</li>
</ol>
</div>""",
            "points": 100
        },
        2: {
            "title": "Activity 2: LED Circuit Building",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Calculate proper resistor values using Ohm's Law</li>
    <li>Build circuits on breadboard</li>
    <li>Understand current limiting</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>Breadboard, LEDs (red, green, blue)</li>
    <li>Resistors (220Ω, 330Ω, 1kΩ)</li>
    <li>Jumper wires, Arduino board</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Calculate resistor for red LED (2V, 20mA) from 5V</td><td>15</td></tr>
    <tr><td>2</td><td>Build single LED circuit with correct resistor</td><td>20</td></tr>
    <tr><td>3</td><td>Build traffic light (3 LEDs) circuit</td><td>25</td></tr>
    <tr><td>4</td><td>Read and identify 5 different resistor values</td><td>20</td></tr>
    <tr><td>5</td><td>Document circuit with schematic drawing</td><td>20</td></tr>
</table>

<h4>Calculation Guide:</h4>
<div class="formula-box">R = (Vsource - Vled) / I<br>R = (5V - 2V) / 0.02A = 150Ω → Use 220Ω (next standard value)</div>
</div>""",
            "points": 100
        },
        3: {
            "title": "Activity 3: Digital Sensors Lab",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Interface digital sensors with Arduino</li>
    <li>Implement pull-up/pull-down resistors</li>
    <li>Process digital sensor data</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>Push buttons (2), PIR sensor, HC-SR04 ultrasonic sensor</li>
    <li>10kΩ resistors, LEDs, Breadboard, Arduino</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Button with external pull-down - LED on when pressed</td><td>20</td></tr>
    <tr><td>2</td><td>Button with internal pull-up - LED toggle</td><td>20</td></tr>
    <tr><td>3</td><td>PIR sensor triggers LED and Serial message</td><td>25</td></tr>
    <tr><td>4</td><td>HC-SR04 displays distance on Serial Monitor</td><td>25</td></tr>
    <tr><td>5</td><td>Combine: Motion activates distance measurement</td><td>10</td></tr>
</table>
</div>""",
            "points": 100
        },
        4: {
            "title": "Activity 4: Analog Sensors Lab",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Understand analog-to-digital conversion</li>
    <li>Interface analog sensors</li>
    <li>Process and display sensor data</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>LM35 temperature sensor, DHT11, LDR, Potentiometer</li>
    <li>10kΩ resistors, LEDs, Arduino</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>LM35: Read temperature, display on Serial</td><td>20</td></tr>
    <tr><td>2</td><td>DHT11: Read temp and humidity (install library)</td><td>25</td></tr>
    <tr><td>3</td><td>LDR: Build voltage divider, read light level</td><td>20</td></tr>
    <tr><td>4</td><td>Potentiometer: Control LED brightness (PWM)</td><td>20</td></tr>
    <tr><td>5</td><td>Create simple weather station display</td><td>15</td></tr>
</table>
</div>""",
            "points": 100
        },
        5: {
            "title": "Activity 5: Output Devices Lab",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Control servo and DC motors</li>
    <li>Use motor driver modules</li>
    <li>Interface LCD displays</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>Servo motor, DC motor, L298N driver</li>
    <li>Relay module, Buzzer, LCD 16x2 I2C</li>
    <li>External power supply</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Servo: Sweep 0° to 180° and back</td><td>20</td></tr>
    <tr><td>2</td><td>DC Motor: Speed control with potentiometer</td><td>25</td></tr>
    <tr><td>3</td><td>Relay: Control LED (simulating appliance)</td><td>20</td></tr>
    <tr><td>4</td><td>Buzzer: Play simple melody</td><td>15</td></tr>
    <tr><td>5</td><td>LCD: Display sensor readings (temp/distance)</td><td>20</td></tr>
</table>
</div>""",
            "points": 100
        },
        6: {
            "title": "Activity 6: System Integration Lab",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Design a complete embedded system</li>
    <li>Integrate multiple sensors and outputs</li>
    <li>Implement serial communication</li>
</ul>

<h4>Project: Smart Environment Monitor</h4>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Draw system block diagram</td><td>15</td></tr>
    <tr><td>2</td><td>List all components with specifications</td><td>15</td></tr>
    <tr><td>3</td><td>Design circuit schematic</td><td>20</td></tr>
    <tr><td>4</td><td>Implement: DHT11 + LDR + LCD + Buzzer</td><td>30</td></tr>
    <tr><td>5</td><td>Serial communication: Send data to PC</td><td>20</td></tr>
</table>

<h4>System Requirements:</h4>
<ul>
    <li>Read temperature and humidity (DHT11)</li>
    <li>Read light level (LDR)</li>
    <li>Display readings on LCD</li>
    <li>Sound buzzer if temp > 35°C</li>
    <li>Send all data via Serial every 5 seconds</li>
</ul>
</div>""",
            "points": 100
        },
        7: {
            "title": "Activity 7: Programming Fundamentals",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Master Arduino programming structure</li>
    <li>Implement control structures and functions</li>
    <li>Work with arrays</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>LED sequence: 5 LEDs light up one by one (Knight Rider)</td><td>25</td></tr>
    <tr><td>2</td><td>Traffic light controller with timing</td><td>25</td></tr>
    <tr><td>3</td><td>Create a function to convert Celsius to Fahrenheit</td><td>15</td></tr>
    <tr><td>4</td><td>Button-controlled LED pattern (3 patterns, cycle on press)</td><td>25</td></tr>
    <tr><td>5</td><td>Serial menu system (user selects option 1-3)</td><td>10</td></tr>
</table>

<h4>Concepts Covered:</h4>
<ul>
    <li>Variables and data types</li>
    <li>Control structures (if/else, for, while, switch)</li>
    <li>Functions with parameters and return values</li>
    <li>Arrays and loops</li>
</ul>
</div>""",
            "points": 100
        },
        8: {
            "title": "Activity 8: Sensor Data Processing and Control",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Process sensor data with filtering</li>
    <li>Implement threshold-based control</li>
    <li>Create state machines</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>Moving average filter: Smooth noisy sensor data</td><td>20</td></tr>
    <tr><td>2</td><td>Threshold control: LED changes color based on temperature ranges</td><td>25</td></tr>
    <tr><td>3</td><td>State machine: 3-state fan controller (OFF, LOW, HIGH)</td><td>30</td></tr>
    <tr><td>4</td><td>Hysteresis: Prevent rapid on/off switching</td><td>15</td></tr>
    <tr><td>5</td><td>Document system behavior with state diagram</td><td>10</td></tr>
</table>
</div>""",
            "points": 100
        },
        9: {
            "title": "Activity 9: Display and User Interface",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Interface various display types</li>
    <li>Create user-friendly interfaces</li>
    <li>Implement menu systems</li>
</ul>

<h4>Materials:</h4>
<ul>
    <li>LCD 16x2 (I2C), OLED SSD1306</li>
    <li>Push buttons, Rotary encoder</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>LCD: Display custom characters and scrolling text</td><td>20</td></tr>
    <tr><td>2</td><td>OLED: Display graphics and sensor data</td><td>25</td></tr>
    <tr><td>3</td><td>Menu system: Navigate with buttons</td><td>25</td></tr>
    <tr><td>4</td><td>Real-time clock display (simulated)</td><td>15</td></tr>
    <tr><td>5</td><td>Settings screen with value adjustment</td><td>15</td></tr>
</table>
</div>""",
            "points": 100
        },
        10: {
            "title": "Activity 10: Serial Communication",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Implement UART, I2C, and SPI communication</li>
    <li>Exchange data between devices</li>
    <li>Create communication protocols</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>UART: Two Arduino boards send/receive data</td><td>20</td></tr>
    <tr><td>2</td><td>I2C: Read data from multiple sensors (same bus)</td><td>25</td></tr>
    <tr><td>3</td><td>SPI: Interface with an SPI device (e.g., SD card module)</td><td>25</td></tr>
    <tr><td>4</td><td>Serial command parser: Execute commands from PC</td><td>20</td></tr>
    <tr><td>5</td><td>Document communication protocol</td><td>10</td></tr>
</table>
</div>""",
            "points": 100
        },
        11: {
            "title": "Activity 11: WiFi and Cloud Connectivity",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Connect ESP32 to WiFi network</li>
    <li>Send data to cloud platforms</li>
    <li>Receive commands from web</li>
</ul>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>WiFi connection: Connect to network, display IP</td><td>15</td></tr>
    <tr><td>2</td><td>HTTP GET: Fetch data from a web API</td><td>20</td></tr>
    <tr><td>3</td><td>HTTP POST: Send sensor data to ThingSpeak</td><td>25</td></tr>
    <tr><td>4</td><td>MQTT: Publish and subscribe to topics</td><td>25</td></tr>
    <tr><td>5</td><td>Create simple web server on ESP32</td><td>15</td></tr>
</table>

<h4>Platforms:</h4>
<ul>
    <li>ThingSpeak for data visualization</li>
    <li>HiveMQ for MQTT broker</li>
    <li>ESP32 built-in web server</li>
</ul>
</div>""",
            "points": 100
        },
        12: {
            "title": "Activity 12: IoT System Integration Project",
            "instructions": """<div class="activity-content">
<h4>Objectives:</h4>
<ul>
    <li>Design and build a complete IoT system</li>
    <li>Integrate sensors, actuators, and cloud</li>
    <li>Implement remote monitoring and control</li>
</ul>

<h4>Final Project: Smart Home/Environment System</h4>

<h4>Tasks:</h4>
<table class="task-table">
    <tr><th>Task</th><th>Description</th><th>Points</th></tr>
    <tr><td>1</td><td>System design document with block diagram</td><td>15</td></tr>
    <tr><td>2</td><td>Hardware assembly with at least 3 sensors</td><td>20</td></tr>
    <tr><td>3</td><td>Local processing and display (LCD/OLED)</td><td>20</td></tr>
    <tr><td>4</td><td>Cloud connectivity (data upload + visualization)</td><td>25</td></tr>
    <tr><td>5</td><td>Remote control capability (web or MQTT)</td><td>20</td></tr>
</table>

<h4>Requirements:</h4>
<ul>
    <li>Minimum 3 sensors (any type)</li>
    <li>At least 1 output device (LED, motor, relay)</li>
    <li>LCD or OLED display for local status</li>
    <li>Cloud data logging (ThingSpeak or similar)</li>
    <li>Mobile/web access for monitoring</li>
</ul>

<h4>Deliverables:</h4>
<ol>
    <li>System design document</li>
    <li>Working prototype</li>
    <li>Demo video (2-3 minutes)</li>
    <li>Code with comments</li>
</ol>
</div>""",
            "points": 100
        }
    }

    # Delete existing ES activities first
    cursor.execute("""
        DELETE FROM activities WHERE session_id IN (
            SELECT id FROM sessions WHERE subject_id = ?
        )
    """, (subject_id,))
    print(f"Deleted existing ES activities")

    # Process each session
    for session_num, activity_data in activities_data.items():
        # Get session ID
        cursor.execute("""
            SELECT id FROM sessions
            WHERE subject_id = ? AND session_number = ?
        """, (subject_id, session_num))
        session_result = cursor.fetchone()

        if not session_result:
            print(f"Session {session_num} not found for ES subject. Skipping...")
            continue

        session_id = session_result['id']

        # Create activity
        cursor.execute("""
            INSERT INTO activities (session_id, activity_number, title, instructions, points)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            1,
            activity_data["title"],
            activity_data["instructions"],
            activity_data["points"]
        ))

        print(f"Created: {activity_data['title']}")

    conn.commit()
    conn.close()
    print("\nES activities seeded successfully with HTML formatting!")

if __name__ == "__main__":
    seed_es_activities()
