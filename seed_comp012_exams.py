"""
Seed script for COMP012 Network Administration Midterm and Final Exams
Creates exams for all 3 COMP012 sections with complete question banks
"""
import sqlite3
import json

DATABASE = 'classroom_lms.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ================== MIDTERM EXAM QUESTIONS ==================

MIDTERM_MULTIPLE_CHOICE = [
    # OSI Model & Networking Basics (Session 1) - Q1-5
    {
        "text": "Which OSI layer is responsible for routing packets between different networks?",
        "options": ["Layer 1 - Physical", "Layer 2 - Data Link", "Layer 3 - Network", "Layer 4 - Transport"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What device operates at Layer 2 and uses MAC addresses to forward frames?",
        "options": ["Router", "Hub", "Switch", "Modem"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which port number is used by HTTPS?",
        "options": ["80", "22", "443", "21"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "How many layers does the TCP/IP model have?",
        "options": ["3", "4", "5", "7"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which protocol provides reliable, connection-oriented data delivery?",
        "options": ["UDP", "ICMP", "TCP", "ARP"],
        "answer": "C",
        "points": 1
    },
    # Network Topology & Simulation (Session 2) - Q6-10
    {
        "text": "Which network topology connects all devices to a central hub or switch?",
        "options": ["Bus", "Ring", "Star", "Mesh"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What type of cable is used to connect a PC directly to a switch?",
        "options": ["Crossover cable", "Straight-through cable", "Rollover cable", "Serial cable"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "In the hierarchical network design, which layer is where end-user devices connect?",
        "options": ["Core layer", "Distribution layer", "Access layer", "Transport layer"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What type of cable is used to connect two similar devices directly (e.g., switch to switch)?",
        "options": ["Straight-through cable", "Crossover cable", "Console cable", "Fiber cable"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which Packet Tracer mode allows you to watch packets travel step-by-step?",
        "options": ["Realtime mode", "Simulation mode", "Debug mode", "Physical mode"],
        "answer": "B",
        "points": 1
    },
    # Switching Fundamentals (Session 3) - Q11-15
    {
        "text": "What does VLAN stand for?",
        "options": ["Virtual Local Area Network", "Very Large Area Network", "Virtual Link Access Node", "Variable LAN"],
        "answer": "A",
        "points": 1
    },
    {
        "text": "Which IEEE standard defines VLAN tagging on trunk links?",
        "options": ["802.11", "802.1Q", "802.3", "802.1X"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What type of switchport mode is used for end devices like PCs?",
        "options": ["Trunk mode", "Access mode", "Dynamic mode", "Hybrid mode"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What is the purpose of a trunk port?",
        "options": ["Connect end-user devices", "Carry traffic for multiple VLANs between switches", "Provide security", "Block unauthorized traffic"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What technique uses a router with subinterfaces to route between VLANs?",
        "options": ["VLAN hopping", "Router-on-a-Stick", "STP", "VTP"],
        "answer": "B",
        "points": 1
    },
    # Routing Fundamentals (Session 4) - Q16-20
    {
        "text": "What type of routing requires manual configuration of routes?",
        "options": ["Dynamic routing", "Static routing", "Default routing", "Automatic routing"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which routing protocol uses hop count as its metric with a maximum of 15 hops?",
        "options": ["OSPF", "EIGRP", "RIP", "BGP"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What is the administrative distance of a directly connected route?",
        "options": ["0", "1", "90", "110"],
        "answer": "A",
        "points": 1
    },
    {
        "text": "Which routing protocol is a link-state protocol that uses cost as its metric?",
        "options": ["RIP", "EIGRP", "OSPF", "BGP"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What is the default route also known as?",
        "options": ["Primary route", "Gateway of last resort", "Backup route", "Main route"],
        "answer": "B",
        "points": 1
    },
    # Windows Server (Session 5) - Q21-25
    {
        "text": "What does AD DS stand for?",
        "options": ["Active Domain Directory Services", "Active Directory Domain Services", "Advanced Directory Domain System", "Active Data Directory Services"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What port does Remote Desktop Protocol (RDP) use?",
        "options": ["22", "443", "3389", "80"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which PowerShell command retrieves all Active Directory users?",
        "options": ["Get-Users", "Get-ADUser -Filter *", "List-ADUsers", "Show-Users"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What is used to organize objects (users, computers) in Active Directory?",
        "options": ["Groups", "Organizational Units (OU)", "Domains", "Forests"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which command creates a new Active Directory user in PowerShell?",
        "options": ["Create-ADUser", "Add-User", "New-ADUser", "Make-ADUser"],
        "answer": "C",
        "points": 1
    },
    # Linux Server (Session 6) - Q26-30
    {
        "text": "Which command displays the current working directory in Linux?",
        "options": ["cd", "pwd", "ls", "dir"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What does the permission value 755 mean for the owner?",
        "options": ["Read only", "Read and write", "Read, write, and execute", "No permissions"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which command changes file permissions in Linux?",
        "options": ["chown", "chmod", "chperm", "chacl"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What directory in Linux contains system configuration files?",
        "options": ["/home", "/var", "/etc", "/bin"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which command updates the package list on Ubuntu?",
        "options": ["apt upgrade", "apt update", "apt install", "apt refresh"],
        "answer": "B",
        "points": 1
    }
]

MIDTERM_TRUE_FALSE = [
    {"text": "A router operates at Layer 3 of the OSI model.", "answer": "TRUE", "points": 1},
    {"text": "In a star topology, if one device fails, the entire network goes down.", "answer": "FALSE", "points": 1},
    {"text": "Devices in different VLANs can communicate directly without a router.", "answer": "FALSE", "points": 1},
    {"text": "OSPF is a Cisco proprietary routing protocol.", "answer": "FALSE", "points": 1},
    {"text": "The root user in Linux has unlimited administrative privileges.", "answer": "TRUE", "points": 1},
    {"text": "A trunk port carries traffic for only one VLAN.", "answer": "FALSE", "points": 1},
    {"text": "TCP is a connectionless protocol.", "answer": "FALSE", "points": 1},
    {"text": "The native VLAN carries untagged traffic on a trunk link.", "answer": "TRUE", "points": 1},
    {"text": "PowerShell's Get-Service command lists all Windows services.", "answer": "TRUE", "points": 1},
    {"text": "The /etc directory in Linux contains user home directories.", "answer": "FALSE", "points": 1}
]

MIDTERM_FILL_BLANK = [
    {"text": "The command to test network connectivity using ICMP is _______.", "answer": "ping", "points": 1},
    {"text": "Port _______ is used for SSH secure remote access.", "answer": "22", "points": 1},
    {"text": "The mnemonic 'Please Do Not Throw Sausage Pizza Away' helps remember the _______ model layers.", "answer": "OSI", "points": 1},
    {"text": "To enter privileged EXEC mode on a Cisco device, type _______.", "answer": "enable", "points": 1},
    {"text": "The command to create a VLAN 10 on a Cisco switch is _______.", "answer": "vlan 10", "points": 1},
    {"text": "To assign a switch port to VLAN 10, use the command: switchport access vlan _______.", "answer": "10", "points": 1},
    {"text": "The command to configure a trunk port is: switchport mode _______.", "answer": "trunk", "points": 1},
    {"text": "A static route command syntax is: ip route [destination] [mask] _______.", "answer": "next-hop", "points": 1},
    {"text": "OSPF stands for Open _______ Path First.", "answer": "Shortest", "points": 1},
    {"text": "In Active Directory, the PowerShell cmdlet to create a new user is _______.", "answer": "New-ADUser", "points": 1},
    {"text": "The Linux command to change file ownership is _______.", "answer": "chown", "points": 1},
    {"text": "The permission value for read (r) is _____, write (w) is _____, execute (x) is _____.", "answer": "4,2,1", "points": 1},
    {"text": "To install a package named 'apache2' on Ubuntu, use: apt _______ apache2.", "answer": "install", "points": 1},
    {"text": "The wildcard mask for subnet 255.255.255.0 is _______.", "answer": "0.0.0.255", "points": 1},
    {"text": "The DHCP process follows the sequence: Discover, Offer, Request, _______.", "answer": "Acknowledge", "points": 1}
]

MIDTERM_MATCHING = [
    {"text": "Port 80", "answer": "HTTP", "points": 1},
    {"text": "Port 443", "answer": "HTTPS", "points": 1},
    {"text": "Port 22", "answer": "SSH", "points": 1},
    {"text": "Port 53", "answer": "DNS", "points": 1},
    {"text": "Port 67", "answer": "DHCP Server", "points": 1},
    {"text": "Layer 1", "answer": "Physical", "points": 1},
    {"text": "Layer 2", "answer": "Data Link", "points": 1},
    {"text": "Layer 3", "answer": "Network", "points": 1},
    {"text": "Layer 4", "answer": "Transport", "points": 1},
    {"text": "Layer 7", "answer": "Application", "points": 1}
]

# ================== FINAL EXAM QUESTIONS ==================

FINAL_MULTIPLE_CHOICE = [
    # Network Services Configuration (Session 7) - Q1-5
    {
        "text": "What does DNS stand for?",
        "options": ["Dynamic Name System", "Domain Name System", "Data Network Service", "Domain Network Server"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What port does DNS use?",
        "options": ["25", "53", "67", "80"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which DNS record type maps a hostname to an IPv4 address?",
        "options": ["MX", "CNAME", "A", "PTR"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What does DHCP stand for?",
        "options": ["Dynamic Host Control Protocol", "Dynamic Host Configuration Protocol", "Domain Host Configuration Protocol", "Data Host Control Protocol"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What is the correct order of the DHCP process?",
        "options": ["Discover, Request, Offer, Acknowledge", "Discover, Offer, Request, Acknowledge", "Request, Discover, Offer, Acknowledge", "Offer, Discover, Request, Acknowledge"],
        "answer": "B",
        "points": 1
    },
    # Network Security and ACLs (Session 8) - Q6-10
    {
        "text": "What does ACL stand for?",
        "options": ["Access Control List", "Advanced Control Layer", "Application Control List", "Automatic Control Logic"],
        "answer": "A",
        "points": 1
    },
    {
        "text": "Which ACL number range is used for Standard ACLs?",
        "options": ["1-99", "100-199", "200-299", "1000-1999"],
        "answer": "A",
        "points": 1
    },
    {
        "text": "Standard ACLs filter traffic based on:",
        "options": ["Destination IP only", "Source IP only", "Source and destination IP", "Port numbers"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What is the implicit rule at the end of every ACL?",
        "options": ["permit any", "deny any", "allow all", "forward all"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Where should a Standard ACL be placed?",
        "options": ["Close to the source", "Close to the destination", "At the core layer", "On the access layer only"],
        "answer": "B",
        "points": 1
    },
    # Cybersecurity Fundamentals (Session 9) - Q11-15
    {
        "text": "What are the three pillars of the CIA Triad?",
        "options": ["Control, Identity, Access", "Confidentiality, Integrity, Availability", "Cybersecurity, Internet, Authentication", "Compliance, Integrity, Authorization"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What is the main difference between IDS and IPS?",
        "options": ["IDS blocks traffic; IPS only alerts", "IDS only alerts; IPS can block traffic", "They are the same", "IDS is for wireless; IPS is for wired"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What does VPN stand for?",
        "options": ["Virtual Private Network", "Very Protected Network", "Virtual Protocol Node", "Verified Private Node"],
        "answer": "A",
        "points": 1
    },
    {
        "text": "What is a DMZ in network security?",
        "options": ["Data Management Zone", "Demilitarized Zone", "Digital Media Zone", "Domain Management Zone"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which security approach assumes no user or device should be trusted by default?",
        "options": ["Defense in Depth", "Zero Trust", "Least Privilege", "Security by Obscurity"],
        "answer": "B",
        "points": 1
    },
    # Python for Network Automation (Session 10) - Q16-20
    {
        "text": "Which Python library is used for SSH connections to network devices?",
        "options": ["requests", "socket", "paramiko", "urllib"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which library simplifies network device automation with a consistent interface?",
        "options": ["paramiko", "netmiko", "pysnmp", "telnetlib"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What Python library is used to connect to Windows servers via WinRM?",
        "options": ["winrm", "pywinrm", "windows-remote", "wmi"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "In Paramiko, which method is used to execute commands on a remote device?",
        "options": ["run_command()", "execute()", "exec_command()", "send_command()"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "In Netmiko, which method sends commands and waits for output?",
        "options": ["exec_command()", "send_command()", "run()", "execute()"],
        "answer": "B",
        "points": 1
    },
    # Python for Cybersecurity (Session 11) - Q21-25
    {
        "text": "Which Python library is used for packet crafting and network analysis?",
        "options": ["nmap", "scapy", "requests", "socket"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What type of scan sends ARP requests to discover live hosts on a network?",
        "options": ["TCP scan", "UDP scan", "ARP scan", "ICMP scan"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "Which Python module is used for creating password hashes?",
        "options": ["crypto", "hash", "hashlib", "encrypt"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What algorithm is commonly used for secure password hashing?",
        "options": ["MD5", "SHA256", "Base64", "AES"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "What does the srp() function in Scapy do?",
        "options": ["Send and receive at Layer 3", "Send and receive at Layer 2", "Scan remote ports", "Sniff packets"],
        "answer": "B",
        "points": 1
    },
    # Cloud Integration & Troubleshooting (Session 12) - Q26-30
    {
        "text": "What does IaaS stand for?",
        "options": ["Internet as a Service", "Infrastructure as a Service", "Integration as a Service", "Information as a Service"],
        "answer": "B",
        "points": 1
    },
    {
        "text": "Which cloud service model provides ready-to-use applications?",
        "options": ["IaaS", "PaaS", "SaaS", "FaaS"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "AWS EC2 is an example of which cloud service model?",
        "options": ["SaaS", "PaaS", "IaaS", "DaaS"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "What is the FIRST step in the troubleshooting methodology?",
        "options": ["Test the theory", "Establish a theory", "Identify the problem", "Implement the solution"],
        "answer": "C",
        "points": 1
    },
    {
        "text": "In the bottom-up troubleshooting approach, which layer is checked first?",
        "options": ["Application layer", "Network layer", "Physical layer", "Transport layer"],
        "answer": "C",
        "points": 1
    }
]

FINAL_TRUE_FALSE = [
    {"text": "DNS translates IP addresses to human-readable domain names.", "answer": "TRUE", "points": 1},
    {"text": "DHCP assigns IP addresses dynamically to network devices.", "answer": "TRUE", "points": 1},
    {"text": "Extended ACLs can filter traffic based on port numbers.", "answer": "TRUE", "points": 1},
    {"text": "IPS is a passive security system that only monitors traffic.", "answer": "FALSE", "points": 1},
    {"text": "A VPN encrypts traffic between two endpoints over a public network.", "answer": "TRUE", "points": 1},
    {"text": "Netmiko is designed specifically for network device automation.", "answer": "TRUE", "points": 1},
    {"text": "Scapy can only capture packets, not create them.", "answer": "FALSE", "points": 1},
    {"text": "PaaS provides a platform for developers to build applications.", "answer": "TRUE", "points": 1},
    {"text": "In Zero Trust security, all users inside the network are trusted by default.", "answer": "FALSE", "points": 1},
    {"text": "The hashlib library in Python is used for encryption, not hashing.", "answer": "FALSE", "points": 1}
]

FINAL_FILL_BLANK = [
    {"text": "The DNS record type used for mail servers is _______.", "answer": "MX", "points": 1},
    {"text": "DHCP uses port _______ for the server and port 68 for the client.", "answer": "67", "points": 1},
    {"text": "The DHCP process follows the acronym D-O-R-A which stands for Discover, Offer, Request, and _______.", "answer": "Acknowledge", "points": 1},
    {"text": "Extended ACLs use numbers in the range of 100 to _______.", "answer": "199", "points": 1},
    {"text": "The command to apply an ACL to an interface inbound is: ip access-group [number] _______.", "answer": "in", "points": 1},
    {"text": "The three pillars of the CIA Triad are Confidentiality, Integrity, and _______.", "answer": "Availability", "points": 1},
    {"text": "A _______ detects intrusions and can actively block malicious traffic.", "answer": "IPS", "points": 1},
    {"text": "To install Netmiko in Python, use the command: pip install _______.", "answer": "netmiko", "points": 1},
    {"text": "In Scapy, the function to send packets at Layer 3 and receive responses is _______.", "answer": "sr", "points": 1},
    {"text": "SHA-256 produces a hash output of 256 bits (or _______ characters in hexadecimal).", "answer": "64", "points": 1},
    {"text": "The cloud service model where you manage applications, data, runtime, and OS is _______.", "answer": "IaaS", "points": 1},
    {"text": "Azure Network _______ Groups are used to filter network traffic to Azure resources.", "answer": "Security", "points": 1},
    {"text": "The troubleshooting methodology step after 'Test the theory' is _______.", "answer": "Establish a plan of action", "points": 1},
    {"text": "The Python library for making HTTP requests to REST APIs is _______.", "answer": "requests", "points": 1},
    {"text": "In network troubleshooting, the command to trace the path packets take to a destination is _______.", "answer": "tracert", "points": 1}
]

FINAL_MATCHING = [
    {"text": "DNS", "answer": "Name to IP translation", "points": 1},
    {"text": "DHCP", "answer": "Automatic IP assignment", "points": 1},
    {"text": "IDS", "answer": "Detects but doesn't block", "points": 1},
    {"text": "VPN", "answer": "Secure encrypted tunnel", "points": 1},
    {"text": "Scapy", "answer": "Packet crafting library", "points": 1},
    {"text": "IaaS", "answer": "Infrastructure as a Service", "points": 1},
    {"text": "SaaS", "answer": "Gmail, Office 365", "points": 1},
    {"text": "Netmiko", "answer": "Network device automation", "points": 1},
    {"text": "PaaS", "answer": "Platform for developers", "points": 1},
    {"text": "Zero Trust", "answer": "Never trust, always verify", "points": 1}
]


def seed_exams():
    conn = get_db()
    cursor = conn.cursor()

    # Get all COMP012 subjects
    cursor.execute("SELECT id, section FROM subjects WHERE code = 'COMP012'")
    comp012_subjects = cursor.fetchall()

    if not comp012_subjects:
        print("No COMP012 subjects found!")
        return

    print(f"Found {len(comp012_subjects)} COMP012 sections")

    for subject in comp012_subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nSeeding exams for {section}...")

        # Check if exams already exist
        cursor.execute("SELECT id FROM exams WHERE subject_id = ? AND exam_type = 'midterm'", (subject_id,))
        existing_midterm = cursor.fetchone()

        cursor.execute("SELECT id FROM exams WHERE subject_id = ? AND exam_type = 'final'", (subject_id,))
        existing_final = cursor.fetchone()

        # Create Midterm Exam if not exists
        if not existing_midterm:
            cursor.execute('''
                INSERT INTO exams (subject_id, exam_type, title, time_limit, total_points)
                VALUES (?, 'midterm', 'COMP012 Midterm Examination - Sessions 1-6', 90, 100)
            ''', (subject_id,))
            midterm_id = cursor.lastrowid
            print(f"  Created Midterm Exam (ID: {midterm_id})")

            # Add Midterm Questions
            # Multiple Choice (30 points)
            for i, q in enumerate(MIDTERM_MULTIPLE_CHOICE, 1):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'multiple_choice', ?, ?, ?)
                ''', (midterm_id, f"{i}. {q['text']}", json.dumps(q['options']), q['answer'], q['points']))

            # True/False (10 points)
            for i, q in enumerate(MIDTERM_TRUE_FALSE, 31):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'true_false', ?, ?, ?)
                ''', (midterm_id, f"{i}. {q['text']}", json.dumps(["TRUE", "FALSE"]), q['answer'], q['points']))

            # Fill in the Blank (15 points)
            for i, q in enumerate(MIDTERM_FILL_BLANK, 41):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'short_answer', ?, ?, ?)
                ''', (midterm_id, f"{i}. {q['text']}", '', q['answer'], q['points']))

            # Matching (10 points)
            for i, q in enumerate(MIDTERM_MATCHING, 56):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'short_answer', ?, ?, ?)
                ''', (midterm_id, f"{i}. Match: {q['text']}", '', q['answer'], q['points']))

            print(f"  Added {len(MIDTERM_MULTIPLE_CHOICE) + len(MIDTERM_TRUE_FALSE) + len(MIDTERM_FILL_BLANK) + len(MIDTERM_MATCHING)} Midterm questions")
        else:
            print(f"  Midterm Exam already exists (ID: {existing_midterm['id']})")

        # Create Final Exam if not exists
        if not existing_final:
            cursor.execute('''
                INSERT INTO exams (subject_id, exam_type, title, time_limit, total_points)
                VALUES (?, 'final', 'COMP012 Final Examination - Sessions 7-12', 90, 100)
            ''', (subject_id,))
            final_id = cursor.lastrowid
            print(f"  Created Final Exam (ID: {final_id})")

            # Add Final Questions
            # Multiple Choice (30 points)
            for i, q in enumerate(FINAL_MULTIPLE_CHOICE, 1):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'multiple_choice', ?, ?, ?)
                ''', (final_id, f"{i}. {q['text']}", json.dumps(q['options']), q['answer'], q['points']))

            # True/False (10 points)
            for i, q in enumerate(FINAL_TRUE_FALSE, 31):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'true_false', ?, ?, ?)
                ''', (final_id, f"{i}. {q['text']}", json.dumps(["TRUE", "FALSE"]), q['answer'], q['points']))

            # Fill in the Blank (15 points)
            for i, q in enumerate(FINAL_FILL_BLANK, 41):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'short_answer', ?, ?, ?)
                ''', (final_id, f"{i}. {q['text']}", '', q['answer'], q['points']))

            # Matching (10 points)
            for i, q in enumerate(FINAL_MATCHING, 56):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, 'short_answer', ?, ?, ?)
                ''', (final_id, f"{i}. Match: {q['text']}", '', q['answer'], q['points']))

            print(f"  Added {len(FINAL_MULTIPLE_CHOICE) + len(FINAL_TRUE_FALSE) + len(FINAL_FILL_BLANK) + len(FINAL_MATCHING)} Final questions")
        else:
            print(f"  Final Exam already exists (ID: {existing_final['id']})")

    conn.commit()
    conn.close()
    print("\n=== COMP012 Exams seeded successfully! ===")


if __name__ == '__main__':
    seed_exams()
