"""
Seed ES (Embedded Systems) Quizzes for Sessions 7-12
Each session has 10 questions covering the session topics
"""

import sqlite3
import json

def seed_es_quizzes_7_12():
    conn = sqlite3.connect('classroom_lms.db')
    cursor = conn.cursor()

    # Get ES subject ID
    cursor.execute("SELECT id FROM subjects WHERE code = 'ES'")
    result = cursor.fetchone()
    if not result:
        print("ES subject not found. Please create the subject first.")
        return

    subject_id = result[0]

    # Session 7-12 Quiz Data
    sessions_data = {
        7: {
            "title": "Arduino Programming Fundamentals",
            "questions": [
                {
                    "question_text": "What function runs once when the Arduino board is powered on or reset?",
                    "question_type": "multiple_choice",
                    "options": ["loop()", "setup()", "main()", "init()"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which function runs continuously after setup() completes?",
                    "question_type": "multiple_choice",
                    "options": ["start()", "run()", "loop()", "execute()"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "What is the correct syntax to set a pin as OUTPUT in Arduino?",
                    "question_type": "multiple_choice",
                    "options": ["setPin(13, OUTPUT)", "pinMode(13, OUTPUT)", "pinOutput(13)", "output(13)"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The delay() function in Arduino uses milliseconds as its unit of time.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "Arduino code is written in a modified version of C/C++.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does digitalWrite(pin, HIGH) do?",
                    "question_type": "multiple_choice",
                    "options": ["Reads the pin state", "Sets pin to 5V/3.3V", "Sets pin to 0V", "Measures voltage"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which statement creates an integer variable in Arduino?",
                    "question_type": "multiple_choice",
                    "options": ["integer x = 5;", "int x = 5;", "num x = 5;", "var x = 5;"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The void keyword means a function does not return a value.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What function reads analog input from a pin?",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "analogRead",
                    "points": 1
                },
                {
                    "question_text": "Serial.begin(9600) sets the baud rate for serial communication to _____ bits per second.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "9600",
                    "points": 1
                }
            ]
        },
        8: {
            "title": "Control Systems and Motor Control",
            "questions": [
                {
                    "question_text": "What component is commonly used to control motor direction and speed?",
                    "question_type": "multiple_choice",
                    "options": ["Resistor", "H-Bridge Motor Driver", "Capacitor", "Diode"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "PWM stands for Pulse Width Modulation.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What is the typical PWM range in Arduino?",
                    "question_type": "multiple_choice",
                    "options": ["0-100", "0-255", "0-1023", "0-512"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which component is used to control the precise angular position of a shaft?",
                    "question_type": "multiple_choice",
                    "options": ["DC Motor", "Stepper Motor", "Servo Motor", "Linear Actuator"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "The L298N is a popular motor driver IC that can control two DC motors.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What Arduino function is used to generate PWM signals?",
                    "question_type": "multiple_choice",
                    "options": ["pwmWrite()", "analogWrite()", "digitalPWM()", "setPWM()"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A relay is an electrically operated switch that can control high-power devices.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What type of motor moves in discrete steps and is ideal for precise positioning?",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Stepper",
                    "points": 1
                },
                {
                    "question_text": "PID control stands for Proportional-Integral-_____.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Derivative",
                    "points": 1
                },
                {
                    "question_text": "Standard hobby servos typically rotate within what range?",
                    "question_type": "multiple_choice",
                    "options": ["0 to 90 degrees", "0 to 180 degrees", "0 to 270 degrees", "0 to 360 degrees"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        9: {
            "title": "Display and User Interface",
            "questions": [
                {
                    "question_text": "What does LCD stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Light Crystal Display", "Liquid Crystal Display", "Led Color Display", "Low Current Display"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "I2C is a communication protocol that requires only 2 wires (SDA and SCL).",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What type of display uses organic compounds that emit light?",
                    "question_type": "multiple_choice",
                    "options": ["LCD", "LED", "OLED", "TFT"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "A 16x2 LCD can display 16 characters on 2 rows.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "Which library is commonly used for I2C LCD displays in Arduino?",
                    "question_type": "multiple_choice",
                    "options": ["LCD_Display.h", "LiquidCrystal_I2C.h", "I2C_Screen.h", "DisplayLib.h"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What function is used to position the cursor on an LCD?",
                    "question_type": "multiple_choice",
                    "options": ["lcd.position()", "lcd.setCursor()", "lcd.moveTo()", "lcd.goto()"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "SSD1306 is a common driver chip for OLED displays.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does TFT stand for in TFT displays?",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Thin Film Transistor",
                    "points": 1
                },
                {
                    "question_text": "The I2C address for most LCD modules is commonly 0x27 or 0x_____.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "3F",
                    "points": 1
                },
                {
                    "question_text": "Seven-segment displays can show numbers and limited letters.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                }
            ]
        },
        10: {
            "title": "Serial Communication",
            "questions": [
                {
                    "question_text": "What does UART stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Universal Async Receive Transmit", "Universal Asynchronous Receiver-Transmitter", "Unified Analog Read Transfer", "Universal Analog Receiver-Transmitter"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Serial communication sends data one bit at a time.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What is the default baud rate commonly used in Arduino Serial communication?",
                    "question_type": "multiple_choice",
                    "options": ["4800", "9600", "19200", "115200"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "SPI communication requires four wires: MOSI, MISO, SCK, and SS.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does SPI stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Serial Port Interface", "Serial Peripheral Interface", "Simple Protocol Interface", "Standard Peripheral Interface"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "In I2C, SDA stands for Serial Data and SCL stands for Serial _____.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Clock",
                    "points": 1
                },
                {
                    "question_text": "The TX pin is used for transmitting data and RX is for receiving.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "Which Arduino function prints data to the Serial Monitor followed by a newline?",
                    "question_type": "multiple_choice",
                    "options": ["Serial.write()", "Serial.print()", "Serial.println()", "Serial.send()"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "MOSI in SPI stands for Master Out Slave _____.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "In",
                    "points": 1
                },
                {
                    "question_text": "I2C can have multiple slave devices on the same bus, each with a unique address.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                }
            ]
        },
        11: {
            "title": "WiFi and Cloud Connectivity",
            "questions": [
                {
                    "question_text": "Which microcontroller is known for its built-in WiFi capability?",
                    "question_type": "multiple_choice",
                    "options": ["Arduino Uno", "ATmega328", "ESP8266/ESP32", "ATtiny85"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "MQTT is a lightweight messaging protocol designed for IoT applications.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does API stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Advanced Programming Interface", "Application Programming Interface", "Automated Process Integration", "Application Protocol Interface"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "HTTP GET requests are used to retrieve data from a server.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "Which cloud platform is commonly used for IoT data visualization?",
                    "question_type": "multiple_choice",
                    "options": ["ThingSpeak", "Microsoft Word", "Adobe Reader", "VLC Player"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "JSON is a data format commonly used in web APIs.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "MQTT uses a publish-subscribe model for communication.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What port is typically used for HTTP connections?",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "80",
                    "points": 1
                },
                {
                    "question_text": "HTTPS uses port _____ for secure connections.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "443",
                    "points": 1
                },
                {
                    "question_text": "Which library is used for WiFi connectivity on ESP32?",
                    "question_type": "multiple_choice",
                    "options": ["Ethernet.h", "WiFi.h", "Network.h", "Internet.h"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        12: {
            "title": "IoT System Integration and Projects",
            "questions": [
                {
                    "question_text": "What is the primary purpose of a gateway in IoT architecture?",
                    "question_type": "multiple_choice",
                    "options": ["Store data locally", "Connect edge devices to the cloud", "Generate power", "Display information"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Edge computing processes data closer to where it is generated.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "Which protocol is commonly used for home automation IoT devices?",
                    "question_type": "multiple_choice",
                    "options": ["FTP", "SMTP", "MQTT", "POP3"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Smart home systems often use voice assistants for control.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does OTA stand for in firmware updates?",
                    "question_type": "multiple_choice",
                    "options": ["Over The Air", "Online Transfer Application", "Open Transfer Access", "Output To Application"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "IoT security is an important consideration in system design.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "A sensor node collects data and sends it to a central system.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "TRUE",
                    "points": 1
                },
                {
                    "question_text": "What does IFTTT stand for in IoT automation?",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "If This Then That",
                    "points": 1
                },
                {
                    "question_text": "The layer in IoT architecture that includes sensors and actuators is called the _____ layer.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Perception",
                    "points": 1
                },
                {
                    "question_text": "Which of these is a popular IoT platform for prototyping?",
                    "question_type": "multiple_choice",
                    "options": ["Photoshop", "Blynk", "Excel", "PowerPoint"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        }
    }

    # Process each session
    for session_num, session_data in sessions_data.items():
        # Get session ID
        cursor.execute("""
            SELECT id FROM sessions
            WHERE subject_id = ? AND session_number = ?
        """, (subject_id, session_num))
        session_result = cursor.fetchone()

        if not session_result:
            print(f"Session {session_num} not found for ES subject. Skipping...")
            continue

        session_id = session_result[0]

        # Check if quiz already exists
        cursor.execute("SELECT id FROM quizzes WHERE session_id = ?", (session_id,))
        existing_quiz = cursor.fetchone()

        if existing_quiz:
            print(f"Quiz already exists for ES Session {session_num}. Skipping...")
            continue

        # Create quiz
        cursor.execute("""
            INSERT INTO quizzes (session_id, title, time_limit)
            VALUES (?, ?, ?)
        """, (session_id, f"Session {session_num}: {session_data['title']}", 15))

        quiz_id = cursor.lastrowid

        # Add questions
        for q in session_data["questions"]:
            options_json = json.dumps(q["options"]) if q["options"] else None
            cursor.execute("""
                INSERT INTO quiz_questions
                (quiz_id, question_text, question_type, options, correct_answer, points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                quiz_id,
                q["question_text"],
                q["question_type"],
                options_json,
                q["correct_answer"],
                q["points"]
            ))

        print(f"Created quiz for ES Session {session_num}: {session_data['title']}")

    conn.commit()
    conn.close()
    print("\nES Sessions 7-12 quizzes seeded successfully!")

if __name__ == "__main__":
    seed_es_quizzes_7_12()
