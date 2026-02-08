"""
Seed ES (Embedded Systems) Midterm and Final Examinations
Midterm: Sessions 1-6 (Hardware Fundamentals) - 100 points
Final: Sessions 7-12 (Programming, Control & Connectivity) - 100 points

Exam Structure:
- Part I: Multiple Choice (30 points)
- Part II: True or False (10 points)
- Part III: Fill in the Blank (15 points)
- Part IV: Matching Type (10 points)
- Part V: Calculations and Circuits (20 points)
- Part VI: Coding and Analysis (15 points)
"""

import sqlite3
import json

def seed_es_exams():
    conn = sqlite3.connect('classroom_lms.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get ES subject ID
    cursor.execute("SELECT id, code FROM subjects WHERE code = 'ES'")
    result = cursor.fetchone()
    if not result:
        print("ES subject not found. Please create the subject first.")
        return

    subject_id = result['id']

    # ==================== MIDTERM EXAMINATION ====================
    # Coverage: Sessions 1-6 - Hardware Fundamentals (15% of Final Grade)
    midterm_data = {
        "exam_type": "midterm",
        "title": "Embedded Systems - Midterm Examination (Sessions 1-6)",
        "time_limit": 90,
        "total_points": 100,
        "questions": [
            # PART I: MULTIPLE CHOICE (30 points) - 1 point each
            # IoT Boards and Architecture (Sessions 1, 6) - Items 1-5
            {"question_text": "Which board has built-in WiFi and Bluetooth capabilities?", "question_type": "multiple_choice", "options": ["Arduino Uno", "Arduino Nano", "ESP32", "Arduino Mega"], "correct_answer": "C", "points": 1},
            {"question_text": "The Arduino Uno uses which microcontroller?", "question_type": "multiple_choice", "options": ["ESP8266", "ATmega328P", "ARM Cortex-M0", "Xtensa LX6"], "correct_answer": "B", "points": 1},
            {"question_text": "How much RAM does the Arduino Uno have?", "question_type": "multiple_choice", "options": ["2 KB", "32 KB", "520 KB", "264 KB"], "correct_answer": "A", "points": 1},
            {"question_text": "Which function runs continuously after setup() in Arduino?", "question_type": "multiple_choice", "options": ["main()", "loop()", "run()", "execute()"], "correct_answer": "B", "points": 1},
            {"question_text": "GPIO stands for:", "question_type": "multiple_choice", "options": ["General Purpose Input/Output", "Ground Power In/Out", "General Pin Interface Operation", "Global Peripheral Input/Output"], "correct_answer": "A", "points": 1},

            # Electronic Components (Session 2) - Items 6-10
            {"question_text": "Using Ohm's Law, if V = 9V and R = 300Ω, what is I?", "question_type": "multiple_choice", "options": ["30 mA", "0.03 A", "2700 A", "Both A and B"], "correct_answer": "D", "points": 1},
            {"question_text": "A resistor with color bands Red-Red-Brown-Gold has what value?", "question_type": "multiple_choice", "options": ["22Ω", "220Ω", "2.2kΩ", "22kΩ"], "correct_answer": "B", "points": 1},
            {"question_text": "The longer leg of an LED is called:", "question_type": "multiple_choice", "options": ["Cathode", "Anode", "Ground", "Base"], "correct_answer": "B", "points": 1},
            {"question_text": "What component stores electrical charge?", "question_type": "multiple_choice", "options": ["Resistor", "Capacitor", "Transistor", "Diode"], "correct_answer": "B", "points": 1},
            {"question_text": "What is the typical forward voltage drop of a red LED?", "question_type": "multiple_choice", "options": ["5V", "3.3V", "2V", "0.7V"], "correct_answer": "C", "points": 1},

            # Digital Sensors (Session 3) - Items 11-15
            {"question_text": "The HC-SR04 ultrasonic sensor measures:", "question_type": "multiple_choice", "options": ["Temperature", "Distance", "Light", "Humidity"], "correct_answer": "B", "points": 1},
            {"question_text": "PIR sensor output when motion is detected is:", "question_type": "multiple_choice", "options": ["Analog varying", "LOW", "HIGH", "PWM"], "correct_answer": "C", "points": 1},
            {"question_text": "When using INPUT_PULLUP, an unpressed button reads:", "question_type": "multiple_choice", "options": ["LOW", "HIGH", "FLOATING", "ANALOG"], "correct_answer": "B", "points": 1},
            {"question_text": "The speed of sound used in HC-SR04 calculations is approximately:", "question_type": "multiple_choice", "options": ["100 m/s", "340 m/s", "1000 m/s", "3000 m/s"], "correct_answer": "B", "points": 1},
            {"question_text": "Which function measures pulse duration in microseconds?", "question_type": "multiple_choice", "options": ["digitalRead()", "analogRead()", "pulseIn()", "measure()"], "correct_answer": "C", "points": 1},

            # Analog Sensors (Session 4) - Items 16-20
            {"question_text": "Arduino Uno's ADC resolution is:", "question_type": "multiple_choice", "options": ["8-bit (0-255)", "10-bit (0-1023)", "12-bit (0-4095)", "16-bit"], "correct_answer": "B", "points": 1},
            {"question_text": "LM35 temperature sensor outputs:", "question_type": "multiple_choice", "options": ["1mV per °C", "10mV per °C", "100mV per °C", "1V per °C"], "correct_answer": "B", "points": 1},
            {"question_text": "When light increases, LDR resistance:", "question_type": "multiple_choice", "options": ["Increases", "Decreases", "Stays constant", "Becomes zero"], "correct_answer": "B", "points": 1},
            {"question_text": "DHT11 sensor measures:", "question_type": "multiple_choice", "options": ["Only temperature", "Only humidity", "Temperature and humidity", "Temperature and pressure"], "correct_answer": "C", "points": 1},
            {"question_text": "What does PWM stand for?", "question_type": "multiple_choice", "options": ["Power Width Modulation", "Pulse Width Modulation", "Pin Width Measurement", "Power Wave Management"], "correct_answer": "B", "points": 1},

            # Output Devices (Session 5) - Items 21-25
            {"question_text": "A standard servo motor typically has a rotation range of:", "question_type": "multiple_choice", "options": ["360° continuous", "0° to 180°", "0° to 90°", "0° to 270°"], "correct_answer": "B", "points": 1},
            {"question_text": "The L298N is used for:", "question_type": "multiple_choice", "options": ["Temperature sensing", "Motor control", "Display interfacing", "Audio output"], "correct_answer": "B", "points": 1},
            {"question_text": "Which Arduino pins support PWM output?", "question_type": "multiple_choice", "options": ["All pins", "Only analog pins", "Pins marked with ~ (3, 5, 6, 9, 10, 11)", "Only digital pins 0-7"], "correct_answer": "C", "points": 1},
            {"question_text": "A relay is best described as:", "question_type": "multiple_choice", "options": ["A type of motor", "An electrically controlled switch", "A temperature sensor", "A display device"], "correct_answer": "B", "points": 1},
            {"question_text": "Which pins are used for I2C communication on Arduino Uno?", "question_type": "multiple_choice", "options": ["D0 and D1", "A4 (SDA) and A5 (SCL)", "D9 and D10", "A0 and A1"], "correct_answer": "B", "points": 1},

            # Communication Protocols (Session 6) - Items 26-30
            {"question_text": "UART communication typically uses how many signal wires?", "question_type": "multiple_choice", "options": ["1", "2 (TX, RX)", "3", "4"], "correct_answer": "B", "points": 1},
            {"question_text": "I2C can address up to how many devices?", "question_type": "multiple_choice", "options": ["8", "16", "127", "255"], "correct_answer": "C", "points": 1},
            {"question_text": "Which protocol is generally the fastest?", "question_type": "multiple_choice", "options": ["UART", "I2C", "SPI", "All are equal"], "correct_answer": "C", "points": 1},
            {"question_text": "Serial.begin(9600) sets the:", "question_type": "multiple_choice", "options": ["Pin number", "Baud rate", "Timeout value", "Buffer size"], "correct_answer": "B", "points": 1},
            {"question_text": "MCU stands for:", "question_type": "multiple_choice", "options": ["Main Control Unit", "Microcontroller Unit", "Motor Control Unit", "Memory Control Unit"], "correct_answer": "B", "points": 1},

            # PART II: TRUE OR FALSE (10 points) - 1 point each
            {"question_text": "ESP32 operates at 3.3V logic level while Arduino Uno operates at 5V.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "A pull-down resistor connects the input pin to VCC (5V).", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "The HC-SR04 ultrasonic sensor has 4 pins: VCC, Trig, Echo, and GND.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "When analogRead() returns 512 on Arduino Uno, the voltage is approximately 2.5V.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "DC motors can be connected directly to Arduino digital pins.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "I2C uses SDA for clock and SCL for data.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "The tone() function can generate different frequencies for a buzzer.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "SPI communication requires 4 wires: MOSI, MISO, SCK, and SS.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "A 16x2 LCD can display 32 characters total (16 per line × 2 lines).", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "Serial.available() returns the number of bytes waiting in the receive buffer.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},

            # PART III: FILL IN THE BLANK (15 points) - 1 point each
            {"question_text": "The formula for Ohm's Law is V = I × _____.", "question_type": "short_answer", "options": None, "correct_answer": "R", "points": 1},
            {"question_text": "To create a development environment for Arduino, the IDE software is called _____.", "question_type": "short_answer", "options": None, "correct_answer": "Arduino IDE", "points": 1},
            {"question_text": "The color code for a 1kΩ resistor is Brown-Black-_____.", "question_type": "short_answer", "options": None, "correct_answer": "Red", "points": 1},
            {"question_text": "Distance formula for HC-SR04: Distance = (Time × 0.034) / _____.", "question_type": "short_answer", "options": None, "correct_answer": "2", "points": 1},
            {"question_text": "The Arduino function to read digital input is _____(pin).", "question_type": "short_answer", "options": None, "correct_answer": "digitalRead", "points": 1},
            {"question_text": "LDR stands for Light _____ Resistor.", "question_type": "short_answer", "options": None, "correct_answer": "Dependent", "points": 1},
            {"question_text": "The Servo library function to set angle position is servo._____(angle).", "question_type": "short_answer", "options": None, "correct_answer": "write", "points": 1},
            {"question_text": "In L298N, the pins IN1 and IN2 control motor _____.", "question_type": "short_answer", "options": None, "correct_answer": "direction", "points": 1},
            {"question_text": "A relay is used to control high-power devices while providing electrical _____.", "question_type": "short_answer", "options": None, "correct_answer": "isolation", "points": 1},
            {"question_text": "The I2C protocol uses a _____-Slave architecture.", "question_type": "short_answer", "options": None, "correct_answer": "Master", "points": 1},
            {"question_text": "DHT11 temperature accuracy is approximately ± _____ °C.", "question_type": "short_answer", "options": None, "correct_answer": "2", "points": 1},
            {"question_text": "PWM pins on Arduino are marked with the _____ symbol.", "question_type": "short_answer", "options": None, "correct_answer": "~", "points": 1},
            {"question_text": "The function to map values from one range to another is _____(value, fromLow, fromHigh, toLow, toHigh).", "question_type": "short_answer", "options": None, "correct_answer": "map", "points": 1},
            {"question_text": "Serial communication speed is measured in _____ (bits per second).", "question_type": "short_answer", "options": None, "correct_answer": "baud", "points": 1},
            {"question_text": "The three main parts of an embedded system are: Inputs, _____, and Outputs.", "question_type": "short_answer", "options": None, "correct_answer": "Processor", "points": 1},

            # PART IV: MATCHING TYPE (10 points) - 1 point each
            {"question_text": "Match: Arduino Uno - Uses _____ microcontroller at 16 MHz.", "question_type": "short_answer", "options": None, "correct_answer": "ATmega328P", "points": 1},
            {"question_text": "Match: ESP32 - Has built-in _____ and Bluetooth.", "question_type": "short_answer", "options": None, "correct_answer": "WiFi", "points": 1},
            {"question_text": "Match: LM35 - Outputs _____ mV per °C.", "question_type": "short_answer", "options": None, "correct_answer": "10", "points": 1},
            {"question_text": "Match: DHT11 - Measures temperature and _____.", "question_type": "short_answer", "options": None, "correct_answer": "humidity", "points": 1},
            {"question_text": "Match: HC-SR04 - Used for _____ measurement.", "question_type": "short_answer", "options": None, "correct_answer": "distance", "points": 1},
            {"question_text": "Match: L298N - Is a _____ driver module.", "question_type": "short_answer", "options": None, "correct_answer": "motor", "points": 1},
            {"question_text": "Match: PIR - Detects _____ using infrared.", "question_type": "short_answer", "options": None, "correct_answer": "motion", "points": 1},
            {"question_text": "Match: Servo - Rotates 0° to _____ degrees.", "question_type": "short_answer", "options": None, "correct_answer": "180", "points": 1},
            {"question_text": "Match: LDR - Senses _____ intensity.", "question_type": "short_answer", "options": None, "correct_answer": "light", "points": 1},
            {"question_text": "Match: Relay - Used for high-power _____.", "question_type": "short_answer", "options": None, "correct_answer": "switching", "points": 1},

            # PART V: CALCULATIONS (20 points) - Various points each
            {"question_text": "LED Circuit: Calculate resistor for LED (Vsupply=5V, Vled=2V, I=20mA). R = (5-2)/0.02 = ?Ω", "question_type": "short_answer", "options": None, "correct_answer": "150", "points": 5},
            {"question_text": "HC-SR04: If pulse duration is 1176µs, calculate distance in cm. (1176 × 0.034) / 2 = ?", "question_type": "short_answer", "options": None, "correct_answer": "20", "points": 5},
            {"question_text": "ADC: If analogRead returns 768, what is the voltage? (768/1023) × 5 = ?V", "question_type": "short_answer", "options": None, "correct_answer": "3.75", "points": 5},
            {"question_text": "LM35: If voltage is 0.35V, what is the temperature? 0.35 × 100 = ?°C", "question_type": "short_answer", "options": None, "correct_answer": "35", "points": 5},

            # PART VI: CODING/ANALYSIS (15 points) - Various points each
            {"question_text": "Code: To set LED_PIN as output, use pinMode(LED_PIN, _____).", "question_type": "short_answer", "options": None, "correct_answer": "OUTPUT", "points": 3},
            {"question_text": "Code: To read analog sensor on A0, use _____(A0).", "question_type": "short_answer", "options": None, "correct_answer": "analogRead", "points": 3},
            {"question_text": "Code: To convert LM35 voltage to temperature, multiply voltage by _____.", "question_type": "short_answer", "options": None, "correct_answer": "100", "points": 3},
            {"question_text": "Code: If potValue=512 and angle=map(potValue,0,1023,0,180), angle = ?", "question_type": "short_answer", "options": None, "correct_answer": "90", "points": 3},
            {"question_text": "System Design: For intruder alert, the sensor that detects motion is called _____ sensor.", "question_type": "short_answer", "options": None, "correct_answer": "PIR", "points": 3}
        ]
    }

    # ==================== FINAL EXAMINATION ====================
    # Coverage: Sessions 7-12 - Programming, Control & Connectivity (15% of Final Grade)
    final_data = {
        "exam_type": "final",
        "title": "Embedded Systems - Final Examination (Sessions 7-12)",
        "time_limit": 90,
        "total_points": 100,
        "questions": [
            # PART I: MULTIPLE CHOICE (30 points)
            # Arduino Programming (Session 7) - Items 1-5
            {"question_text": "Which data type uses 2 bytes and stores integers?", "question_type": "multiple_choice", "options": ["char", "int", "long", "float"], "correct_answer": "B", "points": 1},
            {"question_text": "What value does digitalRead() return when a pin is HIGH?", "question_type": "multiple_choice", "options": ["0", "1", "255", "1023"], "correct_answer": "B", "points": 1},
            {"question_text": "The break statement in a switch-case:", "question_type": "multiple_choice", "options": ["Ends the program", "Exits the current case", "Continues to next case", "Restarts the loop"], "correct_answer": "B", "points": 1},
            {"question_text": "Which loop executes at least once regardless of condition?", "question_type": "multiple_choice", "options": ["for loop", "while loop", "do-while loop", "if statement"], "correct_answer": "C", "points": 1},
            {"question_text": "A function that returns nothing uses which return type?", "question_type": "multiple_choice", "options": ["null", "void", "empty", "none"], "correct_answer": "B", "points": 1},

            # Control Systems (Session 8) - Items 6-10
            {"question_text": "What is the maximum PWM value for analogWrite() in Arduino?", "question_type": "multiple_choice", "options": ["100", "255", "1023", "4095"], "correct_answer": "B", "points": 1},
            {"question_text": "The L298N motor driver can control how many DC motors?", "question_type": "multiple_choice", "options": ["1", "2", "3", "4"], "correct_answer": "B", "points": 1},
            {"question_text": "Which control algorithm uses proportional, integral, and derivative?", "question_type": "multiple_choice", "options": ["PWM", "PID", "ADC", "SPI"], "correct_answer": "B", "points": 1},
            {"question_text": "A state machine is useful for:", "question_type": "multiple_choice", "options": ["Simple on/off control", "Complex multi-state systems", "Analog signal processing", "Power management only"], "correct_answer": "B", "points": 1},
            {"question_text": "Moving average filter is used to:", "question_type": "multiple_choice", "options": ["Amplify signals", "Smooth sensor data", "Generate PWM", "Create delays"], "correct_answer": "B", "points": 1},

            # Display and UI (Session 9) - Items 11-15
            {"question_text": "I2C communication uses how many wires for data transfer?", "question_type": "multiple_choice", "options": ["1", "2", "3", "4"], "correct_answer": "B", "points": 1},
            {"question_text": "What does LCD stand for?", "question_type": "multiple_choice", "options": ["Light Crystal Display", "Liquid Crystal Display", "LED Color Display", "Low Current Display"], "correct_answer": "B", "points": 1},
            {"question_text": "The SSD1306 is a driver chip commonly used for:", "question_type": "multiple_choice", "options": ["LCD", "TFT", "OLED", "E-ink"], "correct_answer": "C", "points": 1},
            {"question_text": "Which function positions the cursor on an LCD display?", "question_type": "multiple_choice", "options": ["lcd.goto()", "lcd.setCursor()", "lcd.moveTo()", "lcd.position()"], "correct_answer": "B", "points": 1},
            {"question_text": "A 16x2 LCD can display how many characters total?", "question_type": "multiple_choice", "options": ["16", "32", "64", "128"], "correct_answer": "B", "points": 1},

            # Serial Communication (Session 10) - Items 16-20
            {"question_text": "What is the default baud rate for Arduino Serial?", "question_type": "multiple_choice", "options": ["4800", "9600", "19200", "115200"], "correct_answer": "B", "points": 1},
            {"question_text": "UART communication is:", "question_type": "multiple_choice", "options": ["Synchronous", "Asynchronous", "Parallel", "Wireless"], "correct_answer": "B", "points": 1},
            {"question_text": "SPI communication uses how many wires (standard)?", "question_type": "multiple_choice", "options": ["2", "3", "4", "5"], "correct_answer": "C", "points": 1},
            {"question_text": "Which Arduino function prints data followed by a newline?", "question_type": "multiple_choice", "options": ["Serial.print()", "Serial.println()", "Serial.write()", "Serial.send()"], "correct_answer": "B", "points": 1},
            {"question_text": "In I2C, what does SCL stand for?", "question_type": "multiple_choice", "options": ["Serial Control Line", "Serial Clock Line", "System Clock", "Sync Clock Level"], "correct_answer": "B", "points": 1},

            # WiFi and Cloud (Session 11) - Items 21-25
            {"question_text": "Which protocol uses publish-subscribe model for IoT?", "question_type": "multiple_choice", "options": ["HTTP", "FTP", "MQTT", "SMTP"], "correct_answer": "C", "points": 1},
            {"question_text": "What does API stand for?", "question_type": "multiple_choice", "options": ["Automated Process Interface", "Application Programming Interface", "Advanced Protocol Integration", "Application Protocol Interface"], "correct_answer": "B", "points": 1},
            {"question_text": "Which HTTP method retrieves data from a server?", "question_type": "multiple_choice", "options": ["POST", "PUT", "DELETE", "GET"], "correct_answer": "D", "points": 1},
            {"question_text": "ThingSpeak is commonly used for:", "question_type": "multiple_choice", "options": ["Video editing", "IoT data visualization", "Game development", "Word processing"], "correct_answer": "B", "points": 1},
            {"question_text": "JSON is a format commonly used for:", "question_type": "multiple_choice", "options": ["Image storage", "Data exchange", "Audio encoding", "Video streaming"], "correct_answer": "B", "points": 1},

            # IoT Integration (Session 12) - Items 26-30
            {"question_text": "What does OTA stand for in firmware updates?", "question_type": "multiple_choice", "options": ["Over The Air", "Online Transfer Application", "Open Technology Access", "Output Terminal Access"], "correct_answer": "A", "points": 1},
            {"question_text": "Edge computing processes data:", "question_type": "multiple_choice", "options": ["Only in the cloud", "At the network edge", "On paper", "Through cables only"], "correct_answer": "B", "points": 1},
            {"question_text": "Which layer in IoT architecture contains sensors?", "question_type": "multiple_choice", "options": ["Application layer", "Network layer", "Perception layer", "Business layer"], "correct_answer": "C", "points": 1},
            {"question_text": "A gateway in IoT architecture:", "question_type": "multiple_choice", "options": ["Stores data only", "Connects edge devices to cloud", "Generates power", "Measures sensors"], "correct_answer": "B", "points": 1},
            {"question_text": "Which platform is popular for IoT automation rules?", "question_type": "multiple_choice", "options": ["Photoshop", "IFTTT", "Excel", "Word"], "correct_answer": "B", "points": 1},

            # PART II: TRUE OR FALSE (10 points)
            {"question_text": "The setup() function runs continuously in Arduino.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "PWM can simulate analog output using digital pins.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "OLED displays require a backlight to function.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "Serial communication sends data one bit at a time.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "The ESP32 cannot connect to WiFi networks.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "MQTT is designed for low-bandwidth IoT applications.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "I2C can support multiple slave devices on the same bus.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "HTTP uses port 443 by default.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "Stepper motors move in discrete steps.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "Edge computing requires all data to be sent to cloud.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},

            # PART III: FILL IN THE BLANK (15 points)
            {"question_text": "The _____ function in Arduino runs repeatedly after setup().", "question_type": "short_answer", "options": None, "correct_answer": "loop", "points": 1},
            {"question_text": "analogWrite() accepts values from 0 to _____.", "question_type": "short_answer", "options": None, "correct_answer": "255", "points": 1},
            {"question_text": "I2C uses SDA (Serial Data) and _____ (Serial Clock).", "question_type": "short_answer", "options": None, "correct_answer": "SCL", "points": 1},
            {"question_text": "The default baud rate for Arduino Serial is _____ bps.", "question_type": "short_answer", "options": None, "correct_answer": "9600", "points": 1},
            {"question_text": "MOSI in SPI stands for Master Out Slave _____.", "question_type": "short_answer", "options": None, "correct_answer": "In", "points": 1},
            {"question_text": "HTTP typically uses port _____ for unsecured connections.", "question_type": "short_answer", "options": None, "correct_answer": "80", "points": 1},
            {"question_text": "HTTPS uses port _____ for secure connections.", "question_type": "short_answer", "options": None, "correct_answer": "443", "points": 1},
            {"question_text": "The L298N can control _____ DC motors simultaneously.", "question_type": "short_answer", "options": None, "correct_answer": "2", "points": 1},
            {"question_text": "LCD stands for _____ Crystal Display.", "question_type": "short_answer", "options": None, "correct_answer": "Liquid", "points": 1},
            {"question_text": "PID stands for Proportional-Integral-_____.", "question_type": "short_answer", "options": None, "correct_answer": "Derivative", "points": 1},
            {"question_text": "UART stands for Universal _____ Receiver-Transmitter.", "question_type": "short_answer", "options": None, "correct_answer": "Asynchronous", "points": 1},
            {"question_text": "SPI stands for Serial _____ Interface.", "question_type": "short_answer", "options": None, "correct_answer": "Peripheral", "points": 1},
            {"question_text": "MQTT uses a publish-_____ messaging model.", "question_type": "short_answer", "options": None, "correct_answer": "subscribe", "points": 1},
            {"question_text": "A 16x2 LCD has 2 rows with _____ characters each.", "question_type": "short_answer", "options": None, "correct_answer": "16", "points": 1},
            {"question_text": "IFTTT stands for If This Then _____.", "question_type": "short_answer", "options": None, "correct_answer": "That", "points": 1},

            # PART IV: MATCHING TYPE (10 points)
            {"question_text": "Match: setup() - Runs _____ when Arduino starts.", "question_type": "short_answer", "options": None, "correct_answer": "once", "points": 1},
            {"question_text": "Match: loop() - Runs _____ after setup.", "question_type": "short_answer", "options": None, "correct_answer": "continuously", "points": 1},
            {"question_text": "Match: pinMode() - Configures pin as input or _____.", "question_type": "short_answer", "options": None, "correct_answer": "output", "points": 1},
            {"question_text": "Match: analogWrite() - Generates _____ signal.", "question_type": "short_answer", "options": None, "correct_answer": "PWM", "points": 1},
            {"question_text": "Match: Serial.begin() - Initializes _____ communication.", "question_type": "short_answer", "options": None, "correct_answer": "serial", "points": 1},
            {"question_text": "Match: WiFi.begin() - Connects to _____ network.", "question_type": "short_answer", "options": None, "correct_answer": "WiFi", "points": 1},
            {"question_text": "Match: lcd.print() - Displays text on _____ screen.", "question_type": "short_answer", "options": None, "correct_answer": "LCD", "points": 1},
            {"question_text": "Match: Servo library - Controls _____ motors.", "question_type": "short_answer", "options": None, "correct_answer": "servo", "points": 1},
            {"question_text": "Match: ThingSpeak - IoT _____ platform.", "question_type": "short_answer", "options": None, "correct_answer": "cloud", "points": 1},
            {"question_text": "Match: MQTT - Lightweight IoT _____ protocol.", "question_type": "short_answer", "options": None, "correct_answer": "messaging", "points": 1},

            # PART V: CALCULATIONS (20 points)
            {"question_text": "PWM: If duty cycle is 50%, what is analogWrite value? (255 × 0.5) = ?", "question_type": "short_answer", "options": None, "correct_answer": "127", "points": 5},
            {"question_text": "Servo: If potValue=256, angle=map(potValue,0,1023,0,180), angle = ?°", "question_type": "short_answer", "options": None, "correct_answer": "45", "points": 5},
            {"question_text": "Timer: millis() returns 5000. How many seconds since startup?", "question_type": "short_answer", "options": None, "correct_answer": "5", "points": 5},
            {"question_text": "Baud: At 9600 baud, how many bytes per second? (9600/10) = ?", "question_type": "short_answer", "options": None, "correct_answer": "960", "points": 5},

            # PART VI: CODING/ANALYSIS (15 points)
            {"question_text": "Code: To initialize serial at 9600, use Serial._____(9600).", "question_type": "short_answer", "options": None, "correct_answer": "begin", "points": 3},
            {"question_text": "Code: To set servo to 90°, use myServo._____(90).", "question_type": "short_answer", "options": None, "correct_answer": "write", "points": 3},
            {"question_text": "Code: To connect WiFi, use WiFi.begin(ssid, _____).", "question_type": "short_answer", "options": None, "correct_answer": "password", "points": 3},
            {"question_text": "Code: To print with newline, use Serial._____(data).", "question_type": "short_answer", "options": None, "correct_answer": "println", "points": 3},
            {"question_text": "Code: const int prevents variable from being _____.", "question_type": "short_answer", "options": None, "correct_answer": "changed", "points": 3}
        ]
    }

    # Process exams
    for exam_data in [midterm_data, final_data]:
        # Check if exam already exists
        cursor.execute("""
            SELECT id FROM exams
            WHERE subject_id = ? AND exam_type = ?
        """, (subject_id, exam_data["exam_type"]))

        existing_exam = cursor.fetchone()
        if existing_exam:
            # Delete existing exam and its questions to update
            exam_id = existing_exam['id']
            cursor.execute("DELETE FROM exam_questions WHERE exam_id = ?", (exam_id,))
            cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            print(f"Deleted existing ES {exam_data['exam_type'].capitalize()} exam for update...")

        # Create exam
        cursor.execute("""
            INSERT INTO exams (subject_id, exam_type, title, time_limit, total_points)
            VALUES (?, ?, ?, ?, ?)
        """, (
            subject_id,
            exam_data["exam_type"],
            exam_data["title"],
            exam_data["time_limit"],
            exam_data["total_points"]
        ))

        exam_id = cursor.lastrowid

        # Add questions
        for q in exam_data["questions"]:
            options_json = json.dumps(q["options"]) if q["options"] else None
            cursor.execute("""
                INSERT INTO exam_questions
                (exam_id, question_text, question_type, options, correct_answer, points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                exam_id,
                q["question_text"],
                q["question_type"],
                options_json,
                q["correct_answer"],
                q["points"]
            ))

        print(f"Created ES {exam_data['exam_type'].capitalize()} exam with {len(exam_data['questions'])} questions ({exam_data['total_points']} points)")

    conn.commit()
    conn.close()
    print("\nES exams seeded successfully!")

if __name__ == "__main__":
    seed_es_exams()
