import os
import subprocess

# We don't have PIL, but we can display the image in Edge and inspect or capture, or use Edge to render the user image and measure where the icon is!
print("User images:")
art_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded"
for f in os.listdir(art_dir):
    print(f, os.path.getsize(os.path.join(art_dir, f)))
