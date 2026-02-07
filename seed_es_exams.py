"""
Seed ES (Embedded Systems) Midterm and Final Examinations
Midterm: Sessions 1-6 (IoT Boards, Components, Digital/Analog Sensors, Output Devices, Architecture)
Final: Sessions 7-12 (Arduino Programming, Control Systems, Displays, Serial Comm, WiFi, IoT Integration)

Each exam has 65 questions:
- 30 Multiple Choice
- 10 True/False
- 15 Fill-in-the-Blank
- 10 Matching
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
    midterm_data = {
        "exam_type": "midterm",
        "title": "Embedded Systems - Midterm Examination",
        "time_limit": 90,
        "total_points": 65,
        "questions": [
            # PART I: Multiple Choice (30 items)
            # IoT Boards (Items 1-5)
            {"question_text": "Which microcontroller board is known for its built-in WiFi and Bluetooth capabilities?", "question_type": "multiple_choice", "options": ["Arduino Uno", "ESP32", "ATmega328P", "PIC16F84"], "correct_answer": "B", "points": 1},
            {"question_text": "The Arduino Uno uses which microcontroller chip?", "question_type": "multiple_choice", "options": ["ESP8266", "STM32", "ATmega328P", "ARM Cortex"], "correct_answer": "C", "points": 1},
            {"question_text": "Which board is best suited for battery-powered wearable devices?", "question_type": "multiple_choice", "options": ["Arduino Mega", "Raspberry Pi 4", "LilyPad Arduino", "BeagleBone"], "correct_answer": "C", "points": 1},
            {"question_text": "The Raspberry Pi is classified as which type of computing device?", "question_type": "multiple_choice", "options": ["Microcontroller", "Single-Board Computer", "FPGA", "ASIC"], "correct_answer": "B", "points": 1},
            {"question_text": "Which ESP board variant is smaller and has fewer GPIO pins?", "question_type": "multiple_choice", "options": ["ESP32", "ESP8266", "ESP32-CAM", "ESP32-WROOM"], "correct_answer": "B", "points": 1},

            # Electronic Components (Items 6-10)
            {"question_text": "What is the primary function of a resistor in a circuit?", "question_type": "multiple_choice", "options": ["Store energy", "Limit current flow", "Amplify signals", "Store charge"], "correct_answer": "B", "points": 1},
            {"question_text": "Which component stores electrical energy in an electric field?", "question_type": "multiple_choice", "options": ["Resistor", "Inductor", "Capacitor", "Transistor"], "correct_answer": "C", "points": 1},
            {"question_text": "A Light Emitting Diode (LED) is what type of component?", "question_type": "multiple_choice", "options": ["Passive", "Active", "Mechanical", "Thermal"], "correct_answer": "B", "points": 1},
            {"question_text": "What determines the color bands on a resistor?", "question_type": "multiple_choice", "options": ["Voltage rating", "Resistance value", "Power rating", "Temperature coefficient"], "correct_answer": "B", "points": 1},
            {"question_text": "Which component acts as an electronic switch?", "question_type": "multiple_choice", "options": ["Capacitor", "Resistor", "Transistor", "Diode"], "correct_answer": "C", "points": 1},

            # Digital Sensors (Items 11-15)
            {"question_text": "Which sensor is commonly used for motion detection in security systems?", "question_type": "multiple_choice", "options": ["LDR", "PIR", "LM35", "DHT11"], "correct_answer": "B", "points": 1},
            {"question_text": "The HC-SR04 ultrasonic sensor measures what parameter?", "question_type": "multiple_choice", "options": ["Temperature", "Distance", "Humidity", "Light intensity"], "correct_answer": "B", "points": 1},
            {"question_text": "A push button is an example of what type of input device?", "question_type": "multiple_choice", "options": ["Analog sensor", "Digital sensor", "Continuous sensor", "Optical sensor"], "correct_answer": "B", "points": 1},
            {"question_text": "The DHT11 sensor measures which two parameters?", "question_type": "multiple_choice", "options": ["Light and sound", "Temperature and humidity", "Pressure and altitude", "Distance and speed"], "correct_answer": "B", "points": 1},
            {"question_text": "Which sensor detects the presence of objects without physical contact?", "question_type": "multiple_choice", "options": ["Push button", "Proximity sensor", "Potentiometer", "Strain gauge"], "correct_answer": "B", "points": 1},

            # Analog Sensors (Items 16-20)
            {"question_text": "What is the output range of Arduino's analog-to-digital converter?", "question_type": "multiple_choice", "options": ["0-255", "0-512", "0-1023", "0-4095"], "correct_answer": "C", "points": 1},
            {"question_text": "An LDR (Light Dependent Resistor) changes its resistance based on:", "question_type": "multiple_choice", "options": ["Temperature", "Humidity", "Light intensity", "Pressure"], "correct_answer": "C", "points": 1},
            {"question_text": "Which component is used to manually adjust voltage levels?", "question_type": "multiple_choice", "options": ["Fixed resistor", "Potentiometer", "Capacitor", "Transistor"], "correct_answer": "B", "points": 1},
            {"question_text": "The LM35 is a popular sensor for measuring:", "question_type": "multiple_choice", "options": ["Humidity", "Pressure", "Temperature", "Light"], "correct_answer": "C", "points": 1},
            {"question_text": "Analog sensors output what type of signal?", "question_type": "multiple_choice", "options": ["Binary (0 or 1)", "Continuous variable", "Pulse width", "Frequency modulated"], "correct_answer": "B", "points": 1},

            # Output Devices (Items 21-25)
            {"question_text": "Which type of motor provides precise angular positioning?", "question_type": "multiple_choice", "options": ["DC Motor", "Stepper Motor", "Servo Motor", "Induction Motor"], "correct_answer": "C", "points": 1},
            {"question_text": "What is the purpose of a motor driver IC like the L293D?", "question_type": "multiple_choice", "options": ["Measure motor speed", "Control motor direction and speed", "Convert AC to DC", "Regulate voltage"], "correct_answer": "B", "points": 1},
            {"question_text": "A buzzer converts electrical signals into:", "question_type": "multiple_choice", "options": ["Light", "Sound", "Heat", "Motion"], "correct_answer": "B", "points": 1},
            {"question_text": "RGB LEDs can produce millions of colors by mixing:", "question_type": "multiple_choice", "options": ["Red, Green, Blue", "Cyan, Magenta, Yellow", "Primary colors only", "Black and white"], "correct_answer": "A", "points": 1},
            {"question_text": "Which device is used to control high-power circuits with low-power signals?", "question_type": "multiple_choice", "options": ["LED", "Relay", "Resistor", "Capacitor"], "correct_answer": "B", "points": 1},

            # System Architecture (Items 26-30)
            {"question_text": "In embedded systems, what does GPIO stand for?", "question_type": "multiple_choice", "options": ["General Purpose Input/Output", "Graphical Processing Interface Option", "Ground Power Input/Output", "General Protocol Interface Operation"], "correct_answer": "A", "points": 1},
            {"question_text": "Which memory type retains data even when power is removed?", "question_type": "multiple_choice", "options": ["RAM", "Cache", "Flash/EEPROM", "Registers"], "correct_answer": "C", "points": 1},
            {"question_text": "The clock speed of a microcontroller is measured in:", "question_type": "multiple_choice", "options": ["Bytes", "Hertz", "Watts", "Ohms"], "correct_answer": "B", "points": 1},
            {"question_text": "Which architecture uses separate buses for instructions and data?", "question_type": "multiple_choice", "options": ["Von Neumann", "Harvard", "RISC", "CISC"], "correct_answer": "B", "points": 1},
            {"question_text": "An interrupt in a microcontroller is used to:", "question_type": "multiple_choice", "options": ["Increase clock speed", "Respond to events immediately", "Store permanent data", "Convert analog to digital"], "correct_answer": "B", "points": 1},

            # PART II: True or False (10 items)
            {"question_text": "The ESP32 has both WiFi and Bluetooth capabilities built-in.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "A capacitor stores energy in a magnetic field.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "PIR sensors can detect motion through walls.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "Analog sensors provide continuous output values.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "Servo motors can rotate 360 degrees continuously.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "The Arduino Uno operates at 5V logic level.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "EEPROM data is lost when power is removed.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "The LDR resistance increases when exposed to more light.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "A relay allows a low-power circuit to control a high-power circuit.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "The Raspberry Pi is a microcontroller board like Arduino.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},

            # PART III: Fill in the Blank (15 items)
            {"question_text": "The _____ sensor is commonly used for non-contact temperature measurement.", "question_type": "short_answer", "options": None, "correct_answer": "infrared", "points": 1},
            {"question_text": "GPIO pins can be configured as either _____ or output.", "question_type": "short_answer", "options": None, "correct_answer": "input", "points": 1},
            {"question_text": "The process of converting analog signals to digital values is called _____ conversion.", "question_type": "short_answer", "options": None, "correct_answer": "analog-to-digital", "points": 1},
            {"question_text": "A _____ is used to limit current flow to an LED.", "question_type": "short_answer", "options": None, "correct_answer": "resistor", "points": 1},
            {"question_text": "The HC-SR04 ultrasonic sensor uses _____ waves to measure distance.", "question_type": "short_answer", "options": None, "correct_answer": "sound", "points": 1},
            {"question_text": "PWM stands for Pulse _____ Modulation.", "question_type": "short_answer", "options": None, "correct_answer": "Width", "points": 1},
            {"question_text": "The ESP8266 microcontroller has built-in _____ connectivity.", "question_type": "short_answer", "options": None, "correct_answer": "WiFi", "points": 1},
            {"question_text": "A _____ motor moves in discrete steps, making it ideal for precise positioning.", "question_type": "short_answer", "options": None, "correct_answer": "stepper", "points": 1},
            {"question_text": "The DHT11 sensor measures both temperature and _____.", "question_type": "short_answer", "options": None, "correct_answer": "humidity", "points": 1},
            {"question_text": "Arduino boards use _____ as their programming language.", "question_type": "short_answer", "options": None, "correct_answer": "C++", "points": 1},
            {"question_text": "A _____ is an electronic component that allows current to flow in one direction only.", "question_type": "short_answer", "options": None, "correct_answer": "diode", "points": 1},
            {"question_text": "The Arduino Uno has _____ analog input pins.", "question_type": "short_answer", "options": None, "correct_answer": "6", "points": 1},
            {"question_text": "IoT stands for Internet of _____.", "question_type": "short_answer", "options": None, "correct_answer": "Things", "points": 1},
            {"question_text": "A _____ circuit is used to divide voltage in electronic circuits.", "question_type": "short_answer", "options": None, "correct_answer": "voltage divider", "points": 1},
            {"question_text": "The unit of electrical resistance is the _____.", "question_type": "short_answer", "options": None, "correct_answer": "ohm", "points": 1},

            # PART IV: Matching (10 items - stored as short_answer with format)
            {"question_text": "Match: ESP32 - This board has built-in WiFi and _____.", "question_type": "short_answer", "options": None, "correct_answer": "Bluetooth", "points": 1},
            {"question_text": "Match: PIR sensor - Detects _____ through infrared radiation.", "question_type": "short_answer", "options": None, "correct_answer": "motion", "points": 1},
            {"question_text": "Match: Capacitor - Stores electrical energy in an electric _____.", "question_type": "short_answer", "options": None, "correct_answer": "field", "points": 1},
            {"question_text": "Match: Transistor - Acts as an electronic _____ or amplifier.", "question_type": "short_answer", "options": None, "correct_answer": "switch", "points": 1},
            {"question_text": "Match: Servo motor - Provides precise _____ control.", "question_type": "short_answer", "options": None, "correct_answer": "angular", "points": 1},
            {"question_text": "Match: LDR - Light _____ Resistor.", "question_type": "short_answer", "options": None, "correct_answer": "Dependent", "points": 1},
            {"question_text": "Match: Relay - Controls high-power devices using _____ signals.", "question_type": "short_answer", "options": None, "correct_answer": "low-power", "points": 1},
            {"question_text": "Match: Ultrasonic sensor - Measures _____ using sound waves.", "question_type": "short_answer", "options": None, "correct_answer": "distance", "points": 1},
            {"question_text": "Match: Potentiometer - Variable _____ used for analog input.", "question_type": "short_answer", "options": None, "correct_answer": "resistor", "points": 1},
            {"question_text": "Match: Flash memory - _____ storage that retains data without power.", "question_type": "short_answer", "options": None, "correct_answer": "Non-volatile", "points": 1}
        ]
    }

    # ==================== FINAL EXAMINATION ====================
    final_data = {
        "exam_type": "final",
        "title": "Embedded Systems - Final Examination",
        "time_limit": 90,
        "total_points": 65,
        "questions": [
            # PART I: Multiple Choice (30 items)
            # Arduino Programming (Items 1-5)
            {"question_text": "Which function runs once when the Arduino board starts?", "question_type": "multiple_choice", "options": ["loop()", "main()", "setup()", "init()"], "correct_answer": "C", "points": 1},
            {"question_text": "The delay(1000) function pauses execution for how long?", "question_type": "multiple_choice", "options": ["1 second", "1 minute", "1 millisecond", "10 seconds"], "correct_answer": "A", "points": 1},
            {"question_text": "Which function sets a pin as input or output?", "question_type": "multiple_choice", "options": ["digitalWrite()", "pinMode()", "analogRead()", "setPin()"], "correct_answer": "B", "points": 1},
            {"question_text": "What value does digitalRead() return when a pin is HIGH?", "question_type": "multiple_choice", "options": ["0", "1", "255", "1023"], "correct_answer": "B", "points": 1},
            {"question_text": "Which keyword is used to create a constant variable in Arduino?", "question_type": "multiple_choice", "options": ["static", "final", "const", "fixed"], "correct_answer": "C", "points": 1},

            # Control Systems (Items 6-10)
            {"question_text": "What is the maximum PWM value for analogWrite() in Arduino?", "question_type": "multiple_choice", "options": ["100", "255", "1023", "4095"], "correct_answer": "B", "points": 1},
            {"question_text": "The L298N motor driver can control how many DC motors?", "question_type": "multiple_choice", "options": ["1", "2", "3", "4"], "correct_answer": "B", "points": 1},
            {"question_text": "Standard hobby servo motors typically rotate within what range?", "question_type": "multiple_choice", "options": ["0-90 degrees", "0-180 degrees", "0-270 degrees", "0-360 degrees"], "correct_answer": "B", "points": 1},
            {"question_text": "Which control algorithm uses proportional, integral, and derivative components?", "question_type": "multiple_choice", "options": ["PWM", "PID", "ADC", "SPI"], "correct_answer": "B", "points": 1},
            {"question_text": "A relay is primarily used to:", "question_type": "multiple_choice", "options": ["Amplify signals", "Store data", "Switch high-power circuits", "Measure voltage"], "correct_answer": "C", "points": 1},

            # Display and UI (Items 11-15)
            {"question_text": "I2C communication uses how many wires for data transfer?", "question_type": "multiple_choice", "options": ["1", "2", "3", "4"], "correct_answer": "B", "points": 1},
            {"question_text": "What does LCD stand for?", "question_type": "multiple_choice", "options": ["Light Crystal Display", "Liquid Crystal Display", "LED Color Display", "Low Current Display"], "correct_answer": "B", "points": 1},
            {"question_text": "The SSD1306 is a driver chip commonly used for which type of display?", "question_type": "multiple_choice", "options": ["LCD", "TFT", "OLED", "E-ink"], "correct_answer": "C", "points": 1},
            {"question_text": "Which function positions the cursor on an LCD display?", "question_type": "multiple_choice", "options": ["lcd.goto()", "lcd.setCursor()", "lcd.moveTo()", "lcd.position()"], "correct_answer": "B", "points": 1},
            {"question_text": "A 16x2 LCD can display how many characters total?", "question_type": "multiple_choice", "options": ["16", "32", "64", "128"], "correct_answer": "B", "points": 1},

            # Serial Communication (Items 16-20)
            {"question_text": "What is the default baud rate for Arduino Serial communication?", "question_type": "multiple_choice", "options": ["4800", "9600", "19200", "115200"], "correct_answer": "B", "points": 1},
            {"question_text": "UART communication is:", "question_type": "multiple_choice", "options": ["Synchronous", "Asynchronous", "Parallel", "Wireless"], "correct_answer": "B", "points": 1},
            {"question_text": "SPI communication uses how many wires (standard)?", "question_type": "multiple_choice", "options": ["2", "3", "4", "5"], "correct_answer": "C", "points": 1},
            {"question_text": "Which Arduino function prints data followed by a newline?", "question_type": "multiple_choice", "options": ["Serial.print()", "Serial.println()", "Serial.write()", "Serial.send()"], "correct_answer": "B", "points": 1},
            {"question_text": "In I2C, what does SCL stand for?", "question_type": "multiple_choice", "options": ["Serial Control Line", "Serial Clock Line", "System Clock", "Sync Clock Level"], "correct_answer": "B", "points": 1},

            # WiFi and Cloud (Items 21-25)
            {"question_text": "Which protocol uses a publish-subscribe model for IoT messaging?", "question_type": "multiple_choice", "options": ["HTTP", "FTP", "MQTT", "SMTP"], "correct_answer": "C", "points": 1},
            {"question_text": "What does API stand for?", "question_type": "multiple_choice", "options": ["Automated Process Interface", "Application Programming Interface", "Advanced Protocol Integration", "Application Protocol Interface"], "correct_answer": "B", "points": 1},
            {"question_text": "Which HTTP method is used to retrieve data from a server?", "question_type": "multiple_choice", "options": ["POST", "PUT", "DELETE", "GET"], "correct_answer": "D", "points": 1},
            {"question_text": "ThingSpeak is commonly used for:", "question_type": "multiple_choice", "options": ["Video editing", "IoT data visualization", "Game development", "Word processing"], "correct_answer": "B", "points": 1},
            {"question_text": "JSON is a format commonly used for:", "question_type": "multiple_choice", "options": ["Image storage", "Data exchange", "Audio encoding", "Video streaming"], "correct_answer": "B", "points": 1},

            # IoT Integration (Items 26-30)
            {"question_text": "What does OTA stand for in firmware updates?", "question_type": "multiple_choice", "options": ["Over The Air", "Online Transfer Application", "Open Technology Access", "Output Terminal Access"], "correct_answer": "A", "points": 1},
            {"question_text": "Edge computing processes data:", "question_type": "multiple_choice", "options": ["Only in the cloud", "At the network edge", "On paper", "Through cables only"], "correct_answer": "B", "points": 1},
            {"question_text": "Which layer in IoT architecture contains sensors and actuators?", "question_type": "multiple_choice", "options": ["Application layer", "Network layer", "Perception layer", "Business layer"], "correct_answer": "C", "points": 1},
            {"question_text": "A gateway in IoT architecture:", "question_type": "multiple_choice", "options": ["Stores data only", "Connects edge devices to cloud", "Generates power", "Measures sensors"], "correct_answer": "B", "points": 1},
            {"question_text": "Which platform is popular for creating IoT automation rules?", "question_type": "multiple_choice", "options": ["Photoshop", "IFTTT", "Excel", "Word"], "correct_answer": "B", "points": 1},

            # PART II: True or False (10 items)
            {"question_text": "The setup() function runs continuously in an Arduino sketch.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "PWM can simulate analog output using digital pins.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "OLED displays require a backlight to function.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "Serial communication sends data one bit at a time.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "The ESP32 cannot connect to WiFi networks.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "MQTT is designed for low-bandwidth IoT applications.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "I2C can support multiple slave devices on the same bus.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "HTTP uses port 443 by default.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},
            {"question_text": "Stepper motors move in discrete steps.", "question_type": "true_false", "options": None, "correct_answer": "TRUE", "points": 1},
            {"question_text": "Edge computing requires all data to be sent to the cloud for processing.", "question_type": "true_false", "options": None, "correct_answer": "FALSE", "points": 1},

            # PART III: Fill in the Blank (15 items)
            {"question_text": "The _____ function in Arduino runs repeatedly after setup() completes.", "question_type": "short_answer", "options": None, "correct_answer": "loop", "points": 1},
            {"question_text": "analogWrite() accepts values from 0 to _____.", "question_type": "short_answer", "options": None, "correct_answer": "255", "points": 1},
            {"question_text": "I2C uses two wires: SDA (Serial Data) and _____ (Serial Clock).", "question_type": "short_answer", "options": None, "correct_answer": "SCL", "points": 1},
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

            # PART IV: Matching (10 items)
            {"question_text": "Match: setup() - Runs _____ when Arduino starts.", "question_type": "short_answer", "options": None, "correct_answer": "once", "points": 1},
            {"question_text": "Match: loop() - Runs _____ after setup completes.", "question_type": "short_answer", "options": None, "correct_answer": "continuously", "points": 1},
            {"question_text": "Match: pinMode() - Configures pin as input or _____.", "question_type": "short_answer", "options": None, "correct_answer": "output", "points": 1},
            {"question_text": "Match: analogWrite() - Generates _____ signal.", "question_type": "short_answer", "options": None, "correct_answer": "PWM", "points": 1},
            {"question_text": "Match: Serial.begin() - Initializes _____ communication.", "question_type": "short_answer", "options": None, "correct_answer": "serial", "points": 1},
            {"question_text": "Match: WiFi.begin() - Connects to _____ network.", "question_type": "short_answer", "options": None, "correct_answer": "WiFi", "points": 1},
            {"question_text": "Match: lcd.print() - Displays text on _____ screen.", "question_type": "short_answer", "options": None, "correct_answer": "LCD", "points": 1},
            {"question_text": "Match: Servo library - Controls _____ motors.", "question_type": "short_answer", "options": None, "correct_answer": "servo", "points": 1},
            {"question_text": "Match: ThingSpeak - IoT _____ platform.", "question_type": "short_answer", "options": None, "correct_answer": "cloud", "points": 1},
            {"question_text": "Match: MQTT - Lightweight IoT _____ protocol.", "question_type": "short_answer", "options": None, "correct_answer": "messaging", "points": 1}
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
            print(f"ES {exam_data['exam_type'].capitalize()} exam already exists. Skipping...")
            continue

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

        print(f"Created ES {exam_data['exam_type'].capitalize()} exam with {len(exam_data['questions'])} questions")

    conn.commit()
    conn.close()
    print("\nES exams seeded successfully!")

if __name__ == "__main__":
    seed_es_exams()
