#!/usr/bin/env python3
"""
Tempo - Student Wellbeing & Deadline Triage Web Server
Serves static assets and provides lightweight REST APIs for AI parsing and data storage.
"""

import http.server
import socketserver
import os
import json
import urllib.parse
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class TempoHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'app': 'Tempo Wellbeing', 'version': '1.0.0'}).encode('utf-8'))
            return
        
        # Default fallback to index.html for root or SPA paths
        if parsed.path in ('', '/', '/emergency', '/stress-check', '/routine', '/hub', '/support', '/admin'):
            self.path = '/index.html'
            
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            body = json.loads(post_data)
        except Exception:
            body = {}

        if parsed.path == '/api/ai/parse-triage':
            # Server-side AI heuristic simulation & task decomposition
            raw_text = body.get('text', '')
            available_hours = body.get('availableHours', 4)
            result = self.simulate_ai_triage(raw_text, available_hours)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def simulate_ai_triage(self, text, available_hours):
        """
        Extract tasks, calculate urgency, and return structured triage plan.
        """
        import re
        lower = text.lower()
        tasks = []
        
        # Simple heuristic parser matching assignments/projects/presentations
        task_patterns = [
            (r'marketing report', 'Marketing Report', 'Tomorrow, 9:00 AM', 2.0, 95),
            (r'\b(?<!marketing\s)report\b', 'Academic Report', 'Tomorrow morning', 2.5, 90),
            (r'presentation|slides', 'Research Presentation Slides', 'Friday, 2:00 PM', 1.5, 75),
            (r'exam|test|quiz|midterm', 'Exam Preparation Review', 'In 3 days', 2.0, 70),
            (r'lab|code|coding', 'Programming Lab Assignment', 'Tonight, 11:59 PM', 1.5, 88),
            (r'essay|paper', 'Course Essay Draft', 'In 2 days', 3.0, 80),
            (r'reading|readings', 'Course Reading Chapters', 'This weekend', 1.0, 50)
        ]
        
        matched_titles = set()
        for pattern, default_title, default_deadline, default_effort, priority in task_patterns:
            if re.search(pattern, lower) and default_title not in matched_titles:
                tasks.append({
                    'id': f'task-{len(tasks) + 1}',
                    'title': default_title,
                    'deadline': default_deadline,
                    'estimatedHours': default_effort,
                    'priorityScore': priority,
                    'status': 'pending'
                })
                matched_titles.add(default_title)
        
        # If no specific known pattern, create sensible parsed task from user's words
        if not tasks:
            clean_snippet = text.strip()[:60] if text.strip() else 'Immediate Academic Task'
            tasks.append({
                'id': 'task-1',
                'title': clean_snippet + '...',
                'deadline': 'Upcoming deadline',
                'estimatedHours': min(available_hours, 2.0),
                'priorityScore': 85,
                'status': 'pending'
            })

        # Sort strictly by priority score (Urgency x Impact)
        tasks.sort(key=lambda t: t['priorityScore'], reverse=True)
        top_task = tasks[0]

        # Generate the ONE Next Action (25 min micro-step)
        if 'marketing' in top_task['title'].lower() or 'report' in top_task['title'].lower():
            one_action = "Write down the 3 core section headings and bullet points for Section 2"
            one_action_micro = "Just open the document and type 3 bullet points for paragraph 1"
            rationale = "This has the earliest deadline (tomorrow morning). Outlining the next section removes 70% of writing hesitation."
        elif 'presentation' in top_task['title'].lower() or 'slide' in top_task['title'].lower():
            one_action = "Create blank slide outline with 5 slide titles (Title, Problem, Method, Findings, Conclusion)"
            one_action_micro = "Open your slide app and title Slide 1 and Slide 2"
            rationale = "Structuring the 5 headers gives you an instant roadmap without needing finished bullet points."
        elif 'lab' in top_task['title'].lower() or 'code' in top_task['title'].lower():
            one_action = "Isolate the failing function and write out input/output test cases on paper"
            one_action_micro = "Add a single print/log statement to verify where the variable changes"
            rationale = "Debugging in code while stressed causes loops. Writing test cases grounds the logic immediately."
        else:
            one_action = f"Draft 3 concrete bullet points for the next section of {top_task['title']}"
            one_action_micro = "Open your notes and read the assignment prompt once with a highlighter"
            rationale = "Starting with a bite-sized draft creates forward momentum without triggering perfectionism."

        return {
            'success': True,
            'summary': f"Detected {len(tasks)} main academic priorities across ~{available_hours} hours available.",
            'availableHours': available_hours,
            'tasks': tasks,
            'topTask': top_task,
            'oneNextAction': one_action,
            'oneNextActionMicro': one_action_micro,
            'rationale': rationale,
            'targetMinutes': 25,
            'recommendedBreakMinutes': 5
        }

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), TempoHandler) as httpd:
        print(f"Tempo Server running at http://localhost:{PORT}")
        print(f"Serving files from {DIRECTORY}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == '__main__':
    run_server()
