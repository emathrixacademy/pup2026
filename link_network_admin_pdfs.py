"""
Script to link PDF files to Network Administration (COMP012) activities.

Place your PDF files in: uploads/activities/Network Administration/
Name them: Session01_xxx.pdf, Session02_xxx.pdf, etc.
OR: Activity1_xxx.pdf, Activity2_xxx.pdf, etc.

The script will link each file to ALL 3 activities in that session.
"""

import sqlite3
import os
import re
import shutil

DATABASE = 'classroom_lms.db'
SOURCE_FOLDER = 'uploads/activities/Network Administration'
DEST_FOLDER = 'static/activity_files'

SUPPORTED_EXTENSIONS = ('.pdf', '.docx', '.doc', '.pptx', '.ppt')

def link_network_admin_pdfs():
    # Ensure destination folder exists
    os.makedirs(DEST_FOLDER, exist_ok=True)

    # Get list of supported files
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Source folder not found: {SOURCE_FOLDER}")
        print("Please create the folder and add your PDF files.")
        return

    doc_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(SUPPORTED_EXTENSIONS)]

    if not doc_files:
        print(f"No files found in {SOURCE_FOLDER}")
        print(f"Supported formats: {SUPPORTED_EXTENSIONS}")
        print("\nPlease add PDF files named like:")
        print("  Session01_Introduction_to_Network_Administration.pdf")
        print("  Session02_IP_Addressing_and_Subnetting.pdf")
        print("  OR")
        print("  Activity1_Network_Administration.pdf")
        print("  Activity2_IP_Addressing.pdf")
        return

    print(f"Found {len(doc_files)} files")

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

    linked_count = 0

    # Process each COMP012 subject
    for subject in subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nProcessing: {section}")

        # Get all sessions for this subject
        cursor.execute("""
            SELECT s.id, s.session_number
            FROM sessions s
            WHERE s.subject_id = ?
            ORDER BY s.session_number
        """, (subject_id,))
        sessions = {row['session_number']: row['id'] for row in cursor.fetchall()}

        for doc_file in doc_files:
            # Extract session number from filename
            # Matches: Session01, Session02, Activity1, Activity2, etc.
            match = re.search(r'[Ss]ession[_]?(\d+)|[Aa]ctivity[_]?(\d+)', doc_file)
            if not match:
                print(f"  Could not extract session number from: {doc_file}")
                continue

            session_num = int(match.group(1) or match.group(2))

            if session_num not in sessions:
                print(f"  Session {session_num} not found for: {doc_file}")
                continue

            session_id = sessions[session_num]

            # Copy file to static folder with COMP012 prefix
            src_path = os.path.join(SOURCE_FOLDER, doc_file)
            dest_filename = f"COMP012_{doc_file}" if not doc_file.startswith("COMP012") else doc_file
            dest_path = os.path.join(DEST_FOLDER, dest_filename)

            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)

            # Update all activities in this session to use this file
            cursor.execute("""
                UPDATE activities
                SET file_path = ?
                WHERE session_id = ?
            """, (dest_filename, session_id))

            linked_count += cursor.rowcount
            print(f"  Session {session_num}: {doc_file} -> {cursor.rowcount} activities")

    conn.commit()
    conn.close()

    print(f"\nDone! Linked {linked_count} activities to files.")
    print("Refresh your browser to see the changes.")

if __name__ == '__main__':
    link_network_admin_pdfs()
