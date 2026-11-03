import sys

with open('planStore.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure CRLF line endings for planStore.js
content = content.replace('\r\n', '\n')

old_save_avail = """        const planId = planData.id || planData.planId || `plan_${planType}_${Date.now()}`;
        const tasks = planData.tasks || (Array.isArray(planData.plannedTasks) ? planData.plannedTasks.map(pt => pt.task).filter(Boolean) : []);
        const fullPlan = {
            id: planId,
            planId: planId,
            planType,
            status: 'active',
            title: planData.title || (planType === 'emergency' ? 'Urgent Plan' : 'Action Plan'),
            totalPlannedMinutes: planData.totalPlannedMinutes || 0,
            tasks,
            plannedTasks: planData.plannedTasks || [],
            unallocatedTasks: planData.unallocatedTasks || [],
            unarrangedTasks: planData.unarrangedTasks || [],
            availabilityDays: planData.availabilityDays || [],
            createdAt: planData.createdAt || new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };"""

new_save_avail = """        const planId = planData.id || planData.planId || `plan_${planType}_${Date.now()}`;
        const tasks = planData.tasks || (Array.isArray(planData.plannedTasks) ? planData.plannedTasks.map(pt => pt.task).filter(Boolean) : []);

        let availDays = planData.availabilityDays;
        if (!Array.isArray(availDays) || availDays.length === 0) {
            try {
                const savedAvail = localStorage.getItem('tempo_availability_days');
                if (savedAvail) availDays = JSON.parse(savedAvail);
            } catch(e) {}
        }
        if (!Array.isArray(availDays)) availDays = [];

        const fullPlan = {
            id: planId,
            planId: planId,
            planType,
            status: 'active',
            title: planData.title || (planType === 'emergency' ? 'Urgent Plan' : 'Action Plan'),
            totalPlannedMinutes: planData.totalPlannedMinutes || 0,
            tasks,
            plannedTasks: planData.plannedTasks || [],
            unallocatedTasks: planData.unallocatedTasks || [],
            unarrangedTasks: planData.unarrangedTasks || [],
            availabilityDays: availDays,
            createdAt: planData.createdAt || new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };"""

if old_save_avail in content:
    content = content.replace(old_save_avail, new_save_avail)
    print("1. Updated saveActivePlan availabilityDays resolution")
else:
    print("WARNING: old_save_avail not found")

old_load_remote_avail = """                            availabilityDays: planRow.metadata?.availabilityDays || [],"""
new_load_remote_avail = """                            availabilityDays: (planRow.metadata?.availabilityDays && planRow.metadata.availabilityDays.length > 0)
                                ? planRow.metadata.availabilityDays
                                : (localPlan?.availabilityDays || []),"""

if old_load_remote_avail in content:
    content = content.replace(old_load_remote_avail, new_load_remote_avail)
    print("2. Updated loadActivePlan remote availabilityDays resolution")

old_load_local_avail = """        if (localPlan && (!localPlan.tasks || localPlan.tasks.length === 0) && Array.isArray(localPlan.plannedTasks)) {
            localPlan.tasks = localPlan.plannedTasks.map(pt => pt.task).filter(Boolean);
        }"""

new_load_local_avail = """        if (localPlan && (!localPlan.tasks || localPlan.tasks.length === 0) && Array.isArray(localPlan.plannedTasks)) {
            localPlan.tasks = localPlan.plannedTasks.map(pt => pt.task).filter(Boolean);
        }
        if (localPlan && (!Array.isArray(localPlan.availabilityDays) || localPlan.availabilityDays.length === 0)) {
            try {
                const savedAvail = localStorage.getItem('tempo_availability_days');
                if (savedAvail) localPlan.availabilityDays = JSON.parse(savedAvail);
            } catch(e) {}
        }"""

if old_load_local_avail in content:
    content = content.replace(old_load_local_avail, new_load_local_avail)
    print("3. Updated loadActivePlan local availabilityDays resolution")

content = content.replace('\n', '\r\n')
with open('planStore.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("planStore.js successfully saved with CRLF line endings!")
