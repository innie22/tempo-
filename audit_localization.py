import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

files_to_check = [
    'index.html',
    'mode.js',
    'stressRelief.js',
    'toolNotes.js',
    'communityPosts.js',
    'focusZone.js',
    'recoverySelfCheck.js',
    'selfCheckWorkspace.js',
    'planWorkspace.js',
    'auth.js',
    'emergencyFlow.js',
    'urmodeFlow.js',
    'unclearMode.js',
    'weeklyReview.js',
    'recoverySetup.js',
    'i18n.js'
]

english_phrases = [
    "Quick Relief", "Focus Now", "Your Working Plan", "Daily Self-check", "Choose a grounding method",
    "Grounded Pause", "Tempo Games", "Gentle Match", "From the Tempo Community", "See all",
    "TASKS", "TASK DONE", "Create Notes", "Tempo break", "Practice Breathing", "Sign In", "Sign Up",
    "Register", "Forgot password", "Search Tempo", "All Durations", "Start this action", "Play",
    "Mindful Break Games", "How are you feeling", "I'm ready", "Try something else",
    "Box Breathing", "Release Tension", "Short Stretch", "Sensory Grounding", "Step Away from Screen",
    "Short Walk", "Write Down Worries", "Get Some Water", "All pairs matched", "Another round",
    "Back to games", "Back to grounding methods", "Back to Tempo Games"
]

print("=== LOCALIZATION AUDIT: TARGET PHRASES ACROSS FILES ===")
for fname in files_to_check:
    if not os.path.exists(fname):
        continue
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    found = []
    for phrase in english_phrases:
        count = content.count(phrase)
        if count > 0:
            found.append(f"{phrase} ({count})")
    if found:
        print(f"\n{fname}:")
        for item in found[:10]:
            print(f"  - {item}")
        if len(found) > 10:
            print(f"  ... and {len(found) - 10} more phrases")
