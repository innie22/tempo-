with open('scratch/verify_multi_account_isolation.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = """            // Verify Alice's task in planStore remains untouched
            const alicePlan = JSON.parse(localStorage.getItem(`tempo_working_plan_${{userAId}}`) || '{{}}');
            const taskAlice = (alicePlan.tasks || []).find(t => t.id === 'task-alice-1');"""

replacement = """            // Verify Alice's task in planStore remains untouched
            const alicePlan = await window.TempoPlanStore.getActivePlan('emergency');
            const taskAlice = (alicePlan && alicePlan.tasks) ? alicePlan.tasks.find(t => t.id === 'task-alice-1') : null;"""

assert target in c, "target not found"
c = c.replace(target, replacement, 1)

with open('scratch/verify_multi_account_isolation.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Step 6 updated successfully.")
