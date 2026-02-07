"""
Seed script for COMP012 - Network Administration Quizzes
Seeds all 12 session quizzes with 10 questions each
"""
import sqlite3
import json

DATABASE = 'classroom_lms.db'

def seed_comp012_quizzes():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all COMP012 subjects
    cursor.execute("SELECT id, section FROM subjects WHERE code = 'COMP012'")
    subjects = cursor.fetchall()

    if not subjects:
        print("COMP012 subjects not found!")
        return

    print(f"Found {len(subjects)} COMP012 subjects (Network Administration)")

    # Quiz data for all 12 sessions
    quizzes_data = {
        1: {
            "title": "Introduction to Network Administration Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "Which OSI layer is responsible for routing packets between networks?",
                    "question_type": "multiple_choice",
                    "options": ["Layer 1 - Physical", "Layer 2 - Data Link", "Layer 3 - Network", "Layer 4 - Transport"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "What device operates at Layer 2 of the OSI model and uses MAC addresses?",
                    "question_type": "multiple_choice",
                    "options": ["Router", "Switch", "Firewall", "Modem"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "TCP is a connectionless protocol that does not guarantee delivery.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "False",
                    "points": 1
                },
                {
                    "question_text": "Which port number is used by HTTP?",
                    "question_type": "multiple_choice",
                    "options": ["21", "22", "80", "443"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "What command is used to test connectivity to another host?",
                    "question_type": "multiple_choice",
                    "options": ["tracert", "ping", "netstat", "ipconfig"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "In the TCP/IP model, how many layers are there?",
                    "question_type": "multiple_choice",
                    "options": ["3", "4", "5", "7"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The protocol used for secure remote access on port 22 is ________.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "SSH",
                    "points": 1
                },
                {
                    "question_text": "Which of the following is a private IP address range?",
                    "question_type": "multiple_choice",
                    "options": ["8.8.8.0/24", "192.168.1.0/24", "172.217.0.0/16", "1.1.1.0/24"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A network administrator is responsible for maintaining, configuring, and troubleshooting network infrastructure.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What does DHCP stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Dynamic Host Configuration Protocol", "Direct Host Control Protocol", "Domain Host Communication Protocol", "Dynamic Hypertext Control Protocol"],
                    "correct_answer": "A",
                    "points": 1
                }
            ]
        },
        2: {
            "title": "Network Topology and Simulation Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "Which network topology has all devices connected to a central hub or switch?",
                    "question_type": "multiple_choice",
                    "options": ["Bus", "Ring", "Star", "Mesh"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "In Cisco Packet Tracer, what type of cable connects a PC directly to a switch?",
                    "question_type": "multiple_choice",
                    "options": ["Crossover cable", "Straight-through cable", "Serial cable", "Fiber cable"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A mesh topology provides the highest redundancy but is the most expensive to implement.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "Which topology connects devices in a circular fashion where data travels in one direction?",
                    "question_type": "multiple_choice",
                    "options": ["Star", "Bus", "Ring", "Hybrid"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "What is the hierarchical network design layer where end-user devices connect?",
                    "question_type": "multiple_choice",
                    "options": ["Core layer", "Distribution layer", "Access layer", "Transport layer"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "In Packet Tracer, what command enters privileged EXEC mode on a Cisco device?",
                    "question_type": "multiple_choice",
                    "options": ["configure terminal", "enable", "login", "admin"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A ________ cable is used to connect two similar devices directly (e.g., PC to PC).",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "crossover",
                    "points": 1
                },
                {
                    "question_text": "Which network topology uses a single cable to connect all devices?",
                    "question_type": "multiple_choice",
                    "options": ["Star", "Bus", "Ring", "Mesh"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "In Packet Tracer, Simulation mode allows you to see packets traveling through the network step by step.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of the Distribution layer in hierarchical network design?",
                    "question_type": "multiple_choice",
                    "options": ["Connect end-user devices", "Provide high-speed backbone", "Route between VLANs and apply policies", "Connect to the internet"],
                    "correct_answer": "C",
                    "points": 1
                }
            ]
        },
        3: {
            "title": "Switching Fundamentals Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does VLAN stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Virtual Local Area Network", "Very Large Area Network", "Virtual Link Access Network", "Verified Local Access Node"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "Which command assigns a switch port to VLAN 10?",
                    "question_type": "multiple_choice",
                    "options": ["vlan 10", "switchport vlan 10", "switchport access vlan 10", "interface vlan 10"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Devices in different VLANs can communicate directly without a router.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "False",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of a trunk port?",
                    "question_type": "multiple_choice",
                    "options": ["Connect end-user devices", "Carry traffic for multiple VLANs between switches", "Provide internet access", "Block unauthorized traffic"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which protocol tags VLAN information on trunk links?",
                    "question_type": "multiple_choice",
                    "options": ["VTP", "STP", "802.1Q", "ARP"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "What command displays VLAN information on a Cisco switch?",
                    "question_type": "multiple_choice",
                    "options": ["show vlans", "show vlan brief", "display vlan", "list vlans"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The technique of using a router with subinterfaces to route between VLANs is called Router-on-a-________.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Stick",
                    "points": 1
                },
                {
                    "question_text": "Which switchport mode is used for connecting to end devices like PCs?",
                    "question_type": "multiple_choice",
                    "options": ["Trunk mode", "Access mode", "Dynamic mode", "Hybrid mode"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The native VLAN carries untagged traffic on a trunk link.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the command to configure a trunk port on a Cisco switch?",
                    "question_type": "multiple_choice",
                    "options": ["switchport mode access", "switchport mode trunk", "switchport trunk enable", "trunk mode on"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        4: {
            "title": "Routing Fundamentals Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What type of routing requires manual configuration of routes?",
                    "question_type": "multiple_choice",
                    "options": ["Dynamic routing", "Static routing", "Default routing", "Automatic routing"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which routing protocol uses hop count as its metric and has a maximum of 15 hops?",
                    "question_type": "multiple_choice",
                    "options": ["OSPF", "EIGRP", "RIP", "BGP"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "OSPF is a link-state routing protocol that uses cost as its metric.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What command displays the routing table on a Cisco router?",
                    "question_type": "multiple_choice",
                    "options": ["show routes", "show ip route", "display routing", "list routes"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which command configures a static route to network 192.168.2.0/24 via 10.0.0.2?",
                    "question_type": "multiple_choice",
                    "options": ["ip route 192.168.2.0 255.255.255.0 10.0.0.2", "route add 192.168.2.0 10.0.0.2", "static route 192.168.2.0/24 10.0.0.2", "ip static 192.168.2.0 10.0.0.2"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "What is a default route also known as?",
                    "question_type": "multiple_choice",
                    "options": ["Primary route", "Gateway of last resort", "Main route", "Backup route"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The command router ospf 1 enables OSPF with process ID ________.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "1",
                    "points": 1
                },
                {
                    "question_text": "Which Cisco proprietary routing protocol uses bandwidth and delay as metrics by default?",
                    "question_type": "multiple_choice",
                    "options": ["RIP", "OSPF", "EIGRP", "IS-IS"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Dynamic routing protocols automatically discover and maintain routes.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the administrative distance of a static route by default?",
                    "question_type": "multiple_choice",
                    "options": ["0", "1", "90", "110"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        5: {
            "title": "Windows Server Fundamentals Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does AD DS stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Active Domain Directory Services", "Active Directory Domain Services", "Advanced Directory Domain System", "Active Data Directory Services"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which PowerShell command lists all Active Directory users?",
                    "question_type": "multiple_choice",
                    "options": ["Get-Users", "Get-ADUser -Filter *", "List-ADUsers", "Show-Users -All"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A Domain Controller stores and manages the Active Directory database.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of an Organizational Unit (OU) in Active Directory?",
                    "question_type": "multiple_choice",
                    "options": ["Store files", "Organize and manage objects like users and computers", "Configure network settings", "Monitor server performance"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which command promotes a Windows Server to a Domain Controller?",
                    "question_type": "multiple_choice",
                    "options": ["Install-ADDSDomainController", "dcpromo", "Add-DomainController", "Both A and B are valid methods"],
                    "correct_answer": "D",
                    "points": 1
                },
                {
                    "question_text": "What port does Remote Desktop Protocol (RDP) use?",
                    "question_type": "multiple_choice",
                    "options": ["22", "80", "443", "3389"],
                    "correct_answer": "D",
                    "points": 1
                },
                {
                    "question_text": "The PowerShell command to create a new AD user is ________-ADUser.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "New",
                    "points": 1
                },
                {
                    "question_text": "Which Windows Server role provides centralized authentication and authorization?",
                    "question_type": "multiple_choice",
                    "options": ["DNS Server", "DHCP Server", "Active Directory Domain Services", "File Server"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Group Policy can be used to enforce security settings across multiple computers in a domain.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the command to view all running services in PowerShell?",
                    "question_type": "multiple_choice",
                    "options": ["Get-Service", "List-Services", "Show-Service -All", "View-Services"],
                    "correct_answer": "A",
                    "points": 1
                }
            ]
        },
        6: {
            "title": "Linux Server Fundamentals Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "Which command displays the current working directory in Linux?",
                    "question_type": "multiple_choice",
                    "options": ["cd", "pwd", "dir", "ls"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What command is used to create a new user in Linux?",
                    "question_type": "multiple_choice",
                    "options": ["newuser", "useradd or adduser", "createuser", "mkuser"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The root user in Linux has unlimited administrative privileges.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "Which command changes file permissions in Linux?",
                    "question_type": "multiple_choice",
                    "options": ["chown", "chmod", "chperm", "perm"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What does the permission value 755 mean?",
                    "question_type": "multiple_choice",
                    "options": ["Owner: read/write, Group: read, Others: read", "Owner: read/write/execute, Group: read/execute, Others: read/execute", "Owner: full, Group: none, Others: none", "Everyone has full access"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which command updates package lists on Ubuntu/Debian?",
                    "question_type": "multiple_choice",
                    "options": ["apt upgrade", "apt update", "apt refresh", "apt sync"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The command to change a file's owner is ________.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "chown",
                    "points": 1
                },
                {
                    "question_text": "What is the default shell in most Linux distributions?",
                    "question_type": "multiple_choice",
                    "options": ["sh", "csh", "bash", "zsh"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "The /etc directory contains system configuration files.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "Which command displays disk space usage in human-readable format?",
                    "question_type": "multiple_choice",
                    "options": ["disk -h", "df -h", "du -h", "space -h"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        7: {
            "title": "Network Services Configuration Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does DNS stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Dynamic Name System", "Domain Name System", "Directory Name Service", "Distributed Network System"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which DNS record type maps a hostname to an IP address?",
                    "question_type": "multiple_choice",
                    "options": ["MX", "CNAME", "A", "PTR"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "DHCP automatically assigns IP addresses to network clients.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the default port for DNS?",
                    "question_type": "multiple_choice",
                    "options": ["23", "53", "67", "80"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which Windows Server role is used to host websites?",
                    "question_type": "multiple_choice",
                    "options": ["Active Directory", "IIS (Internet Information Services)", "DNS Server", "File Server"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What protocol is used for Windows file sharing?",
                    "question_type": "multiple_choice",
                    "options": ["NFS", "FTP", "SMB", "HTTP"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "A DHCP ________ is a range of IP addresses that can be assigned to clients.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "scope",
                    "points": 1
                },
                {
                    "question_text": "Which command installs Apache web server on Ubuntu?",
                    "question_type": "multiple_choice",
                    "options": ["apt install apache", "apt install apache2", "apt install httpd", "apt install webserver"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "A PTR record is used for reverse DNS lookups (IP to hostname).",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What DHCP option number specifies the default gateway?",
                    "question_type": "multiple_choice",
                    "options": ["Option 003", "Option 006", "Option 015", "Option 044"],
                    "correct_answer": "A",
                    "points": 1
                }
            ]
        },
        8: {
            "title": "Network Security and ACLs Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does ACL stand for in networking?",
                    "question_type": "multiple_choice",
                    "options": ["Automatic Control List", "Access Control List", "Advanced Configuration Layer", "Application Control Logic"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which type of ACL filters traffic based on source IP address only?",
                    "question_type": "multiple_choice",
                    "options": ["Extended ACL", "Standard ACL", "Named ACL", "Dynamic ACL"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Extended ACLs can filter traffic based on source IP, destination IP, protocol, and port numbers.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the range for standard ACL numbers on Cisco devices?",
                    "question_type": "multiple_choice",
                    "options": ["1-99", "100-199", "200-299", "1-999"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "Which command applies an ACL to an interface (inbound)?",
                    "question_type": "multiple_choice",
                    "options": ["access-list apply in", "ip access-group 10 in", "acl 10 inbound", "apply access-list 10 in"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What is the implicit rule at the end of every ACL?",
                    "question_type": "multiple_choice",
                    "options": ["Permit any", "Deny any", "Log all", "Forward all"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The wildcard mask 0.0.0.255 is equivalent to subnet mask ________.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "255.255.255.0",
                    "points": 1
                },
                {
                    "question_text": "Which command enables the firewall on Ubuntu?",
                    "question_type": "multiple_choice",
                    "options": ["firewall-cmd --enable", "ufw enable", "iptables --start", "systemctl start firewall"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Port security on a switch can limit the number of MAC addresses allowed on a port.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of security hardening?",
                    "question_type": "multiple_choice",
                    "options": ["Increase network speed", "Reduce vulnerabilities and attack surface", "Add more features", "Improve user experience"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        9: {
            "title": "Cybersecurity Fundamentals Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does CIA stand for in cybersecurity?",
                    "question_type": "multiple_choice",
                    "options": ["Central Intelligence Agency", "Confidentiality, Integrity, Availability", "Computer Information Access", "Cybersecurity Infrastructure Assessment"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What type of attack floods a target with traffic to make it unavailable?",
                    "question_type": "multiple_choice",
                    "options": ["Phishing", "Man-in-the-Middle", "DDoS (Distributed Denial of Service)", "SQL Injection"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "An IDS (Intrusion Detection System) can actively block malicious traffic.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "False",
                    "points": 1
                },
                {
                    "question_text": "What is a DMZ in network security?",
                    "question_type": "multiple_choice",
                    "options": ["A type of firewall", "A network segment for public-facing servers", "A VPN protocol", "An encryption standard"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which type of VPN connects two networks securely over the internet?",
                    "question_type": "multiple_choice",
                    "options": ["Remote Access VPN", "Site-to-Site VPN", "SSL VPN", "Personal VPN"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What protocol suite does IPSec VPN use for encryption?",
                    "question_type": "multiple_choice",
                    "options": ["SSL/TLS", "ESP and AH", "PPTP", "HTTP"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The security principle that gives users only the minimum access needed is called ________ of Least Privilege.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "Principle",
                    "points": 1
                },
                {
                    "question_text": "What is the difference between IDS and IPS?",
                    "question_type": "multiple_choice",
                    "options": ["IDS is faster", "IPS can block traffic; IDS only detects and alerts", "IDS encrypts traffic", "They are the same"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Social engineering attacks exploit human psychology rather than technical vulnerabilities.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What does the Zero Trust security model assume?",
                    "question_type": "multiple_choice",
                    "options": ["All internal traffic is safe", "Never trust, always verify", "External traffic is dangerous", "Firewalls are unnecessary"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        10: {
            "title": "Python for Network Automation Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "Which Python library is used for SSH connections to network devices?",
                    "question_type": "multiple_choice",
                    "options": ["requests", "paramiko", "socket", "http"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What does the socket module in Python provide?",
                    "question_type": "multiple_choice",
                    "options": ["Web scraping", "Low-level network communication", "Database connections", "File encryption"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Netmiko is a Python library built on top of Paramiko for network device automation.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "Which command installs Paramiko using pip?",
                    "question_type": "multiple_choice",
                    "options": ["pip install ssh", "pip install paramiko", "pip install netmiko", "pip install pyssh"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What method is used to execute a command on a remote device using Paramiko?",
                    "question_type": "multiple_choice",
                    "options": ["run_command()", "exec_command()", "send_command()", "execute()"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which library is used to connect to Windows servers using WinRM?",
                    "question_type": "multiple_choice",
                    "options": ["paramiko", "pywinrm", "winssh", "winconnect"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "To read output from a Paramiko SSH command, you use stdout.________()",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "read",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of the requests library in Python?",
                    "question_type": "multiple_choice",
                    "options": ["SSH connections", "HTTP requests to web APIs", "Database queries", "File operations"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Python scripts can be used to automate repetitive network tasks like backups and health checks.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "Which Python data format is commonly used for storing device inventories?",
                    "question_type": "multiple_choice",
                    "options": ["XML only", "CSV, JSON, or YAML", "Binary files", "Plain text only"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        11: {
            "title": "Python for Cybersecurity Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "Which Python library is commonly used for packet capture and analysis?",
                    "question_type": "multiple_choice",
                    "options": ["requests", "scapy", "paramiko", "flask"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What does the nmap library in Python provide?",
                    "question_type": "multiple_choice",
                    "options": ["File encryption", "Network scanning and port discovery", "Web development", "Database management"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Scapy can be used to create, send, and capture network packets.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What type of scan checks if a port is open by completing the TCP handshake?",
                    "question_type": "multiple_choice",
                    "options": ["SYN scan", "UDP scan", "TCP Connect scan", "Ping scan"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Which Python function would you use to generate a hash of a password?",
                    "question_type": "multiple_choice",
                    "options": ["hash()", "hashlib.sha256()", "encrypt()", "encode()"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What does ARP stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Address Resolution Protocol", "Automatic Routing Protocol", "Advanced Resource Protocol", "Application Request Protocol"],
                    "correct_answer": "A",
                    "points": 1
                },
                {
                    "question_text": "A ________ scan discovers live hosts on a network by sending ICMP requests.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "ping",
                    "points": 1
                },
                {
                    "question_text": "Which Python library is used for SSL/TLS certificate verification?",
                    "question_type": "multiple_choice",
                    "options": ["paramiko", "ssl", "scapy", "requests"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Python scripts should only be used to scan networks you own or have permission to test.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the purpose of the hashlib module in Python?",
                    "question_type": "multiple_choice",
                    "options": ["Network scanning", "Creating cryptographic hashes (MD5, SHA256)", "File compression", "Web scraping"],
                    "correct_answer": "B",
                    "points": 1
                }
            ]
        },
        12: {
            "title": "Cloud Integration and Troubleshooting Quiz",
            "time_limit": 15,
            "questions": [
                {
                    "question_text": "What does EC2 stand for in AWS?",
                    "question_type": "multiple_choice",
                    "options": ["Elastic Cloud Computing", "Elastic Compute Cloud", "Enterprise Cloud Container", "External Compute Cluster"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which cloud service model provides virtual machines that you manage?",
                    "question_type": "multiple_choice",
                    "options": ["SaaS", "PaaS", "IaaS", "FaaS"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "A Security Group in AWS acts as a virtual firewall for EC2 instances.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What is the first step in the network troubleshooting methodology?",
                    "question_type": "multiple_choice",
                    "options": ["Replace hardware", "Identify the problem", "Test the solution", "Document the issue"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "Which command shows the path packets take to reach a destination?",
                    "question_type": "multiple_choice",
                    "options": ["ping", "traceroute / tracert", "netstat", "ifconfig"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "What does hybrid cloud infrastructure mean?",
                    "question_type": "multiple_choice",
                    "options": ["Using only public cloud", "Combining on-premises and cloud resources", "Using multiple cloud providers", "Private cloud only"],
                    "correct_answer": "B",
                    "points": 1
                },
                {
                    "question_text": "The command ________ -an displays all network connections and listening ports.",
                    "question_type": "fill_in_blank",
                    "options": None,
                    "correct_answer": "netstat",
                    "points": 1
                },
                {
                    "question_text": "Which OSI layer should you check first when troubleshooting (bottom-up approach)?",
                    "question_type": "multiple_choice",
                    "options": ["Application (Layer 7)", "Network (Layer 3)", "Physical (Layer 1)", "Transport (Layer 4)"],
                    "correct_answer": "C",
                    "points": 1
                },
                {
                    "question_text": "Azure NSG (Network Security Group) is similar to AWS Security Groups.",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "points": 1
                },
                {
                    "question_text": "What command releases and renews a DHCP lease on Windows?",
                    "question_type": "multiple_choice",
                    "options": ["ipconfig /release then ipconfig /renew", "dhcp release then dhcp renew", "netsh dhcp release", "ip release then ip renew"],
                    "correct_answer": "A",
                    "points": 1
                }
            ]
        }
    }

    # Process each subject
    for subject in subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nProcessing: Network Administration - {section}")

        # Get sessions for this subject
        cursor.execute("SELECT id, session_number FROM sessions WHERE subject_id = ? ORDER BY session_number", (subject_id,))
        sessions = cursor.fetchall()

        # Create quizzes for sessions 1-12
        for session in sessions:
            session_num = session['session_number']
            session_id = session['id']

            if session_num in quizzes_data:
                quiz_data = quizzes_data[session_num]

                # Check if quiz already exists
                cursor.execute("SELECT id FROM quizzes WHERE session_id = ?", (session_id,))
                existing = cursor.fetchone()

                if existing:
                    # Delete existing quiz and questions
                    cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (existing['id'],))
                    cursor.execute("DELETE FROM quizzes WHERE id = ?", (existing['id'],))

                # Create quiz
                cursor.execute('''
                    INSERT INTO quizzes (session_id, title, time_limit)
                    VALUES (?, ?, ?)
                ''', (session_id, quiz_data['title'], quiz_data['time_limit']))

                quiz_id = cursor.lastrowid

                # Add questions
                for q in quiz_data['questions']:
                    options_json = json.dumps(q['options']) if q['options'] else None
                    cursor.execute('''
                        INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (quiz_id, q['question_text'], q['question_type'], options_json, q['correct_answer'], q['points']))

                print(f"  Session {session_num}: {quiz_data['title']} ({len(quiz_data['questions'])} questions)")

    conn.commit()
    conn.close()
    print("\n" + "="*60)
    print("All COMP012 (Network Administration) quizzes seeded successfully!")
    print("="*60)

if __name__ == '__main__':
    seed_comp012_quizzes()
