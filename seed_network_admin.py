import sqlite3

DATABASE = 'classroom_lms.db'

def seed_network_admin_activities():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get ALL COMP012 subjects (Network Administration)
    cursor.execute("SELECT id, section FROM subjects WHERE code = 'COMP012'")
    subjects = cursor.fetchall()
    if not subjects:
        print("COMP012 subjects not found!")
        return

    print(f"Found {len(subjects)} COMP012 subjects (Network Administration)")

    # COMP012 - Network Administration Activities (1 activity per session)
    activities_data = {
        1: {"title": "Introduction to Network Administration", "activity": ("Session 1 Activity", "Complete the activities in the attached PDF file.", 100)},
        2: {"title": "Network Topology and Simulation", "activity": ("Session 2 Activity", "Complete the activities in the attached PDF file.", 100)},
        3: {"title": "Switching Fundamentals", "activity": ("Session 3 Activity", "Complete the activities in the attached PDF file.", 100)},
        4: {"title": "Routing Fundamentals", "activity": ("Session 4 Activity", "Complete the activities in the attached PDF file.", 100)},
        5: {"title": "Windows Server Fundamentals", "activity": ("Session 5 Activity", "Complete the activities in the attached PDF file.", 100)},
        6: {"title": "Linux Server Fundamentals", "activity": ("Session 6 Activity", "Complete the activities in the attached PDF file.", 100)},
        7: {"title": "Network Services Configuration", "activity": ("Session 7 Activity", "Complete the activities in the attached PDF file.", 100)},
        8: {"title": "Network Security and ACLs", "activity": ("Session 8 Activity", "Complete the activities in the attached PDF file.", 100)},
        9: {"title": "Cybersecurity Fundamentals", "activity": ("Session 9 Activity", "Complete the activities in the attached PDF file.", 100)},
        10: {"title": "Python for Network Automation", "activity": ("Session 10 Activity", "Complete the activities in the attached PDF file.", 100)},
        11: {"title": "Python for Cybersecurity", "activity": ("Session 11 Activity", "Complete the activities in the attached PDF file.", 100)},
        12: {"title": "Cloud Integration and Troubleshooting", "activity": ("Session 12 Activity", "Complete the activities in the attached PDF file.", 100)},
        13: {"title": "Project Sprint 1 - Foundation", "activity": ("Session 13 Activity", "Complete the activities in the attached PDF file.", 100)},
        14: {"title": "Project Sprint 2 - Core Features", "activity": ("Session 14 Activity", "Complete the activities in the attached PDF file.", 100)},
        15: {"title": "Project Sprint 3 - Integration and Testing", "activity": ("Session 15 Activity", "Complete the activities in the attached PDF file.", 100)},
        16: {"title": "Final Presentation and Defense", "activity": ("Session 16 Activity", "Complete the activities in the attached PDF file.", 100)},
    }

    # Process each COMP012 subject
    for subject in subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nProcessing: Network Administration - {section}")

        # Get all sessions for this subject
        cursor.execute("SELECT id, session_number FROM sessions WHERE subject_id = ? ORDER BY session_number", (subject_id,))
        sessions = cursor.fetchall()

        # Delete existing activities for these sessions
        for session in sessions:
            cursor.execute("DELETE FROM activities WHERE session_id = ?", (session['id'],))
        print(f"  Cleared existing activities for {section}...")

        # Update session titles and insert activities (1 per session)
        for session in sessions:
            session_num = session['session_number']
            session_id = session['id']

            if session_num in activities_data:
                data = activities_data[session_num]

                # Update session title
                cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (data['title'], session_id))

                # Insert single activity
                title, instructions, points = data['activity']
                cursor.execute('''
                    INSERT INTO activities (session_id, activity_number, title, instructions, points)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, 1, title, instructions, points))
                print(f"  Added Session {session_num}: {data['title']}")

    conn.commit()
    conn.close()
    print("\nAll COMP012 (Network Administration) activities seeded successfully!")

if __name__ == '__main__':
    seed_network_admin_activities()
