# 🌿 Tempo — Student Wellbeing & Deadline Triage

> *"Help the student regain control of the immediate situation first, then help them understand and manage their stress in the longer term."*

**Tempo** is an interactive, compassionate academic support system designed for university students facing concentrated deadline clusters, exam anxiety, and academic burnout. 

Unlike conventional productivity tools that exacerbate guilt, or generic meditation apps that ignore pressing assignment due dates, Tempo combines **acute deadline stabilization**, **progressive crisis grounding**, and **flexible, non-judgmental habit building**.

---

## ✨ Core Features

1. **Progressive Emergency & Crisis Support Suite**
   - Multi-stage check-in (`Overwhelmed`, `Emotional Crisis`, `Self-harm / Suicide`, `Not Sure`).
   - Grounding activities (Sensory 3-item scan, visually paced 4-4-4-4 breathing circle, physical safety orientation).
   - Dual-rail architecture: Persistent Human Support Drawer (`988 Lifeline`, `741741 Crisis Text Line`, campus clinic offline notice, and copyable trusted-friend message).
   - Bridge into practical problem decomposition and the **ONE Next Action**.

2. **AI Emergency Triage Engine**
   - Natural language brain dump parser.
   - Deterministic deadline urgency matrix ($Urgency \times Impact$).
   - High-prominence **ONE Next Action** card (with a *"Make it even smaller (5 mins)"* hurdle-reduction button).
   - Distraction-free 25-minute gentle focus timer with built-in Web Audio ambient sound synthesizers (*Gentle Rain*, *Forest Breeze*, *Deep White Noise*).

3. **Personalized Routine & Habit Tracker (Anti-Guilt UX)**
   - Daily stress-management habits (*Morning Hydration*, *Box Breathing*, *Outdoor Walk*, *Bedtime Paper Dump*).
   - Non-punitive 7-day gentle momentum dots (no harsh broken-streak penalties).
   - **"Take a Rest Day (Zero Pressure)"** mode celebrating rest as an active recovery habit.
   - Pre-curated stress-relief habit library for 1-click addition.

4. **6-Dimension Stress Self-Assessment**
   - Real-time tactile sliders (*Perceived Stress*, *Deadline Pressure*, *Sleep Quality*, *Concentration*, *Exhaustion*, *Burnout Signs*).
   - Dynamic SVG Radar / Spider Web visualization.
   - Non-clinical categorization and tailored next-step actions based on highest strain.

5. **"Learn & Solve" Knowledge Hub**
   - 3-minute actionable guides for acute student friction points.
   - Filterable by pain state (*Can't Start*, *Asking for Help*, *Sleep & Worry*, *Brain Fog*).
   - Includes 1-click copyable professor extension request email template.

6. **Human Support & Advisor Portal**
   - Role switcher toggle: `[🎓 Student View]` $\leftrightarrow$ `[👩‍🏫 Advisor: Dr. Elena Vance]`.
   - Support ticket inquiry queue with 1-click empathetic advisor response templates (*Extension Strategy*, *De-escalation*, *Drop-in Offer*).
   - Micro-tip authoring and publishing system that updates the student feed in real time.

---

## 🔒 Safety & Non-Clinical Ethics Guardrails

* **Zero Clinical Diagnosis:** The system strictly avoids medical or psychiatric diagnostic terminology (e.g., claiming a student has Major Depressive Disorder, GAD, or ADHD).
* **Human-Centered Escalation:** AI never positions itself as a replacement for clinical emergency services. Immediate human helplines (988, 741741) remain accessible 1 click away on every screen.
* **Realistic Institution Hours:** Clearly indicates when university staff are offline (outside 9am–5pm) so students in acute distress are directed to 24/7 hotlines rather than waiting on emails.

---

## 🚀 Instant Deployment to Vercel

Tempo is engineered with zero-bundler friction and deploys out-of-the-box to **Vercel**:

### Option 1: Deploy via Vercel Web Dashboard (Recommended)
1. Push this repository to your GitHub account (see instructions below).
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **"Add New Project"** $\rightarrow$ select your imported `tempo-wellbeing` repository.
4. Keep the default settings (**Framework Preset: Other**).
5. Click **Deploy**. Your application will be live on a secure `.vercel.app` URL in under 20 seconds!

### Option 2: Deploy via Vercel CLI
```bash
npm i -g vercel
vercel
```

---

## 💻 Local Development Setup

No heavy node package installation required:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tempo-wellbeing.git
cd tempo-wellbeing

# Run the local Python server
python server.py
# Or on Windows:
py -3 server.py
```

Open your browser at **http://localhost:8000**.

---

## 🛠️ Tech Stack & Architecture

* **Frontend:** Clean Semantic HTML5, Tailwind CSS, Google Fonts (*Plus Jakarta Sans* & *Inter*), Native Web Audio API synthesis.
* **Architecture:** Modular client-side state engines with LocalStorage persistence.
* **Backend / APIs:** 
  * Local: Python 3 HTTP Server (`server.py`).
  * Cloud: Vercel Serverless Functions (`/api/ai/parse-triage.js`, `/api/health.js`).
* **Deployment:** Vercel Static & Serverless Edge Platform (`vercel.json`).

---

## 📄 License
MIT License. Created to support student mental wellbeing and academic calm.
