"""
Seed script for ES (Embedded Systems) Quizzes - Sessions 1-6
Creates quizzes for the ES subject with complete question banks
"""
import sqlite3
import json

DATABASE = 'classroom_lms.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Session 1: Introduction to Embedded Systems & IoT Boards
SESSION1_QUIZ = {
    "title": "Quiz 1: Introduction to Embedded Systems",
    "questions": [
        {
            "text": "An embedded system is best described as:",
            "type": "multiple_choice",
            "options": ["A general-purpose computer", "A computer designed for specific dedicated functions", "A gaming console", "A web server"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which Arduino board has built-in WiFi and Bluetooth?",
            "type": "multiple_choice",
            "options": ["Arduino Uno", "Arduino Nano", "ESP32", "Arduino Mega"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "The ATmega328P microcontroller in Arduino Uno operates at:",
            "type": "multiple_choice",
            "options": ["8 MHz", "16 MHz", "240 MHz", "133 MHz"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "How much RAM does the Arduino Uno have?",
            "type": "multiple_choice",
            "options": ["2 KB", "32 KB", "520 KB", "264 KB"],
            "answer": "A",
            "points": 1
        },
        {
            "text": "Which pin type is used to read sensors that output varying voltages?",
            "type": "multiple_choice",
            "options": ["Digital pins", "Analog pins", "Power pins", "Ground pins"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The ESP32 uses which type of processor?",
            "type": "multiple_choice",
            "options": ["8-bit AVR", "32-bit Xtensa", "64-bit ARM", "16-bit PIC"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What is the default blink delay in the Arduino example sketch?",
            "type": "multiple_choice",
            "options": ["500 ms", "1000 ms", "100 ms", "2000 ms"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which function runs once when the Arduino starts?",
            "type": "multiple_choice",
            "options": ["loop()", "main()", "setup()", "start()"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "What voltage does Arduino Uno operate at?",
            "type": "multiple_choice",
            "options": ["3.3V only", "5V", "12V", "9V"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "GPIO stands for:",
            "type": "multiple_choice",
            "options": ["General Purpose Input/Output", "Ground Power Input/Output", "General Peripheral Interface Operation", "Global Pin Input/Output"],
            "answer": "A",
            "points": 1
        }
    ]
}

# Session 2: Electronic Components and Circuit Basics
SESSION2_QUIZ = {
    "title": "Quiz 2: Electronic Components",
    "questions": [
        {
            "text": "Which component limits current flow in a circuit?",
            "type": "multiple_choice",
            "options": ["Capacitor", "Resistor", "Transistor", "Diode"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Using Ohm's Law, if V=5V and R=1000Ω, what is I?",
            "type": "multiple_choice",
            "options": ["5000 A", "0.005 A (5 mA)", "500 A", "0.5 A"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "A resistor with bands Brown-Black-Red-Gold has what value?",
            "type": "multiple_choice",
            "options": ["100Ω", "1,000Ω (1kΩ)", "10,000Ω", "10Ω"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What is the typical forward voltage of a red LED?",
            "type": "multiple_choice",
            "options": ["5V", "3.3V", "1.8-2.2V", "0.7V"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "Which component stores electrical charge?",
            "type": "multiple_choice",
            "options": ["Resistor", "Capacitor", "Transistor", "LED"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The longer leg of an LED is the:",
            "type": "multiple_choice",
            "options": ["Cathode (negative)", "Anode (positive)", "Ground", "Signal"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What resistor value should be used for an LED (2V, 20mA) with 5V supply?",
            "type": "multiple_choice",
            "options": ["100Ω", "150Ω (use 220Ω)", "1000Ω", "50Ω"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "A transistor can be used as:",
            "type": "multiple_choice",
            "options": ["A switch or amplifier", "Only a resistor", "A power source", "A display"],
            "answer": "A",
            "points": 1
        },
        {
            "text": "In a breadboard, which rows are typically connected?",
            "type": "multiple_choice",
            "options": ["Rows a-e on same row number", "All rows vertically", "Only power rails", "None are connected"],
            "answer": "A",
            "points": 1
        },
        {
            "text": "What does the gold band on a resistor indicate?",
            "type": "multiple_choice",
            "options": ["0 value", "±5% tolerance", "1MΩ multiplier", "Temperature rating"],
            "answer": "B",
            "points": 1
        }
    ]
}

# Session 3: Digital Sensors
SESSION3_QUIZ = {
    "title": "Quiz 3: Digital Sensors",
    "questions": [
        {
            "text": "A digital signal can have:",
            "type": "multiple_choice",
            "options": ["Infinite values", "Only HIGH or LOW states", "Values from 0-255", "Negative values only"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "When using INPUT_PULLUP, an unpressed button reads:",
            "type": "multiple_choice",
            "options": ["LOW", "HIGH", "FLOATING", "ANALOG"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The PIR sensor HC-SR501 detects:",
            "type": "multiple_choice",
            "options": ["Light intensity", "Temperature", "Motion/movement", "Sound"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "How many pins does the HC-SR04 ultrasonic sensor have?",
            "type": "multiple_choice",
            "options": ["2", "3", "4", "6"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "The Trig pin on HC-SR04 is used to:",
            "type": "multiple_choice",
            "options": ["Receive echo signal", "Send ultrasonic pulse", "Power the sensor", "Ground connection"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "If HC-SR04 echo time is 580 µs, what is the distance?",
            "type": "multiple_choice",
            "options": ["5 cm", "10 cm", "20 cm", "58 cm"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "A pull-down resistor connects the pin to:",
            "type": "multiple_choice",
            "options": ["VCC (5V)", "Ground (0V)", "Another pin", "The button"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "PIR sensor output is:",
            "type": "multiple_choice",
            "options": ["Analog (0-1023)", "Digital (HIGH/LOW)", "PWM signal", "I2C data"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What function reads the duration of a pulse on a pin?",
            "type": "multiple_choice",
            "options": ["digitalRead()", "analogRead()", "pulseIn()", "duration()"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "The speed of sound used for HC-SR04 calculation is approximately:",
            "type": "multiple_choice",
            "options": ["340 m/s (0.034 cm/µs)", "100 m/s", "1000 m/s", "3000 m/s"],
            "answer": "A",
            "points": 1
        }
    ]
}

# Session 4: Analog Sensors
SESSION4_QUIZ = {
    "title": "Quiz 4: Analog Sensors",
    "questions": [
        {
            "text": "Arduino Uno's ADC resolution is:",
            "type": "multiple_choice",
            "options": ["8-bit (0-255)", "10-bit (0-1023)", "12-bit (0-4095)", "16-bit (0-65535)"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "If analogRead() returns 512, what is the approximate voltage?",
            "type": "multiple_choice",
            "options": ["1.0V", "2.5V", "3.3V", "5.0V"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The LM35 temperature sensor outputs:",
            "type": "multiple_choice",
            "options": ["1mV per °C", "10mV per °C", "100mV per °C", "1V per °C"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "DHT11 measures:",
            "type": "multiple_choice",
            "options": ["Only temperature", "Only humidity", "Temperature and humidity", "Pressure and temperature"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "When more light hits an LDR, its resistance:",
            "type": "multiple_choice",
            "options": ["Increases", "Decreases", "Stays the same", "Becomes infinite"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The map() function is used to:",
            "type": "multiple_choice",
            "options": ["Create a geographic map", "Scale values from one range to another", "Store data in memory", "Connect to GPS"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "PWM stands for:",
            "type": "multiple_choice",
            "options": ["Power Width Modulation", "Pulse Width Modulation", "Pin Width Measurement", "Power Wave Management"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which pin would you use for PWM output on Arduino Uno?",
            "type": "multiple_choice",
            "options": ["A0", "Pin 7", "Pin 9 (marked with ~)", "Pin 12"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "MQ-2 gas sensor is typically used to detect:",
            "type": "multiple_choice",
            "options": ["Oxygen levels", "Smoke and combustible gases", "Water vapor", "CO2 only"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What component is needed with an LDR to create a voltage divider?",
            "type": "multiple_choice",
            "options": ["Capacitor", "Transistor", "Fixed resistor", "LED"],
            "answer": "C",
            "points": 1
        }
    ]
}

# Session 5: Output Devices and Actuators
SESSION5_QUIZ = {
    "title": "Quiz 5: Output Devices",
    "questions": [
        {
            "text": "Why can't a DC motor be connected directly to an Arduino pin?",
            "type": "multiple_choice",
            "options": ["It needs more current than Arduino can supply", "Motors only work with batteries", "Arduino doesn't have enough pins", "Motors need AC power"],
            "answer": "A",
            "points": 1
        },
        {
            "text": "A standard servo motor typically rotates:",
            "type": "multiple_choice",
            "options": ["360° continuously", "0° to 180°", "0° to 90° only", "0° to 270°"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The L298N is a:",
            "type": "multiple_choice",
            "options": ["Temperature sensor", "Motor driver module", "Display controller", "Power supply"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What does a relay do?",
            "type": "multiple_choice",
            "options": ["Measures voltage", "Acts as an electrically controlled switch", "Converts AC to DC", "Amplifies signals"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which Arduino pins are used for I2C communication?",
            "type": "multiple_choice",
            "options": ["D0 and D1", "A4 (SDA) and A5 (SCL)", "D9 and D10", "All analog pins"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The tone() function is used to:",
            "type": "multiple_choice",
            "options": ["Play audio files", "Generate square wave frequencies on a pin", "Record sound", "Communicate with speakers"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "L298N's ENA pin controls:",
            "type": "multiple_choice",
            "options": ["Motor direction", "Motor speed via PWM", "Power supply", "Ground connection"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "A 16x2 LCD can display:",
            "type": "multiple_choice",
            "options": ["16 characters on 2 lines", "2 characters on 16 lines", "32 characters on 1 line", "Images and video"],
            "answer": "A",
            "points": 1
        },
        {
            "text": "To control motor direction with L298N, you change:",
            "type": "multiple_choice",
            "options": ["ENA value", "IN1 and IN2 states", "Power supply voltage", "PWM frequency"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "The Servo library function to set position is:",
            "type": "multiple_choice",
            "options": ["servo.position()", "servo.write()", "servo.move()", "servo.set()"],
            "answer": "B",
            "points": 1
        }
    ]
}

# Session 6: System Architecture and Communication
SESSION6_QUIZ = {
    "title": "Quiz 6: System Architecture",
    "questions": [
        {
            "text": "UART communication uses how many wires (excluding ground)?",
            "type": "multiple_choice",
            "options": ["1", "2 (TX and RX)", "3", "4"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "I2C can connect up to how many devices on one bus?",
            "type": "multiple_choice",
            "options": ["2", "8", "127", "Unlimited"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "Which protocol is fastest?",
            "type": "multiple_choice",
            "options": ["UART", "I2C", "SPI", "They are all the same"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "The function Serial.begin(9600) sets the:",
            "type": "multiple_choice",
            "options": ["Pin number", "Baud rate", "Data size", "Timeout value"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "In I2C, SDA stands for:",
            "type": "multiple_choice",
            "options": ["Serial Data Access", "Serial Data", "Synchronized Data Address", "System Data Allocation"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which component is NOT typically an input device?",
            "type": "multiple_choice",
            "options": ["DHT11 sensor", "Push button", "Relay module", "Ultrasonic sensor"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "Serial.available() returns:",
            "type": "multiple_choice",
            "options": ["True or False", "Number of bytes available to read", "The baud rate", "The port number"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "What is the first step in embedded system design?",
            "type": "multiple_choice",
            "options": ["Buy components", "Write code", "Define requirements", "Build the circuit"],
            "answer": "C",
            "points": 1
        },
        {
            "text": "MCU stands for:",
            "type": "multiple_choice",
            "options": ["Main Control Unit", "Microcontroller Unit", "Motor Control Unit", "Memory Control Unit"],
            "answer": "B",
            "points": 1
        },
        {
            "text": "Which is true about SPI communication?",
            "type": "multiple_choice",
            "options": ["It uses only 2 wires", "It's slower than I2C", "It uses separate wires for input and output (MOSI/MISO)", "It can only connect 1 device"],
            "answer": "C",
            "points": 1
        }
    ]
}

ALL_SESSIONS = [
    (1, SESSION1_QUIZ),
    (2, SESSION2_QUIZ),
    (3, SESSION3_QUIZ),
    (4, SESSION4_QUIZ),
    (5, SESSION5_QUIZ),
    (6, SESSION6_QUIZ),
]


def seed_quizzes():
    conn = get_db()
    cursor = conn.cursor()

    # Get ES subject
    cursor.execute("SELECT id, section FROM subjects WHERE code = 'ES'")
    es_subjects = cursor.fetchall()

    if not es_subjects:
        print("No ES subjects found!")
        return

    print(f"Found {len(es_subjects)} ES section(s)")

    for subject in es_subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nSeeding quizzes for ES - {section}...")

        for session_num, quiz_data in ALL_SESSIONS:
            # Get the session for this subject
            cursor.execute('''
                SELECT id FROM sessions
                WHERE subject_id = ? AND session_number = ?
            ''', (subject_id, session_num))
            session = cursor.fetchone()

            if not session:
                print(f"  Session {session_num} not found, skipping...")
                continue

            session_id = session['id']

            # Check if quiz already exists
            cursor.execute('''
                SELECT id FROM quizzes WHERE session_id = ?
            ''', (session_id,))
            existing_quiz = cursor.fetchone()

            if existing_quiz:
                print(f"  Session {session_num} quiz already exists, skipping...")
                continue

            # Create quiz
            cursor.execute('''
                INSERT INTO quizzes (session_id, title, time_limit)
                VALUES (?, ?, 15)
            ''', (session_id, quiz_data['title']))
            quiz_id = cursor.lastrowid

            # Add questions
            for q in quiz_data['questions']:
                options_json = json.dumps(q['options']) if q.get('options') else ''
                cursor.execute('''
                    INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (quiz_id, q['text'], q['type'], options_json, q['answer'], q['points']))

            print(f"  Created {quiz_data['title']} with {len(quiz_data['questions'])} questions")

    conn.commit()
    conn.close()
    print("\n=== ES Quizzes seeded successfully! ===")


if __name__ == '__main__':
    seed_quizzes()
