/**
 * Tempo Centralized Plan & Task Persistence Store
 * File: planStore.js
 * 
 * Architecture:
 * - Dual-layer persistence: Supabase remote tables + localStorage synchronous write-through cache & offline/dev fallback.
 * - Single stable identity for Shared Tasks across Emergency Plan, Recovery Plan, Unclear Plan, and Focus Zone.
 * - Normalized Plan Items layer preserving plan-specific execution order and scheduling.
 * - Full draft autosave and restoration across page reload, mode switching, and session resume.
 */

window.TempoPlanStore = (function() {
    const STORAGE_PREFIX = 'tempo_store_';

    // In-memory runtime cache for quick synchronous access
    let activePlans = {};  // planType -> planData
    let activeDrafts = {}; // planType -> draftData
    let isInitialized = false;

    // Helper: current user ID or 'guest'
    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function') {
            const user = window.TempoAuth.getCurrentUser();
            if (user && user.id) return user.id;
        }
        return 'guest';
    }

    // Helper: Supabase client if connected
    function getSupabase() {
        if (window.TempoSupabase && typeof window.TempoSupabase.getClient === 'function' && window.TempoSupabase.hasConnection()) {
            return window.TempoSupabase.getClient();
        }
        return null;
    }

    function isRemoteAvailable() {
        const client = getSupabase();
        const userId = getUserId();
        return !!(client && userId && userId !== 'guest');
    }

    // Cache key helpers
    function getDraftKey(userId, planType) {
        return `${STORAGE_PREFIX}draft_${planType}_${userId || 'guest'}`;
    }

    function getActiveKey(userId, planType) {
        return `${STORAGE_PREFIX}active_${planType}_${userId || 'guest'}`;
    }

    function getSharedTasksKey(userId) {
        return `${STORAGE_PREFIX}tasks_${userId || 'guest'}`;
    }

    // =========================================================================
    // DATA CONVERTERS: JS CAMELCASE MODEL <-> POSTGRES SNAKE_CASE SCHEMA
    // =========================================================================

    function mapDbTaskToModel(dbTask, subtasks = []) {
        if (!dbTask) return null;
        return {
            id: dbTask.id,
            name: dbTask.name || '',
            description: dbTask.description || '',
            hasDeadline: !!dbTask.has_deadline,
            deadlineDate: dbTask.deadline_date || '',
            deadlineTime: dbTask.deadline_time || '',
            importance: dbTask.importance || 'High',
            consequence: dbTask.consequence || 'Big consequences',
            flexibility: Array.isArray(dbTask.flexibility) ? dbTask.flexibility : [],
            durationMinutes: typeof dbTask.duration_minutes === 'number' ? dbTask.duration_minutes : 60,
            durationLabel: dbTask.duration_label || '1h',
            isUnknownDuration: !!dbTask.is_unknown_duration,
            isLongTerm: !!dbTask.is_long_term,
            priorityCategory: dbTask.priority_category || 'DO_FIRST',
            executionStatus: dbTask.execution_status || 'not_started',
            completed: !!dbTask.completed,
            isInProgress: !!dbTask.is_in_progress,
            isBrokenDown: !!dbTask.is_broken_down,
            alreadyKnowWhatToDo: !!dbTask.already_know_what_to_do,
            subtasks: subtasks.map(mapDbSubtaskToModel)
        };
    }

    function mapModelToDbTask(task, userId) {
        return {
            id: task.id,
            user_id: userId,
            name: task.name || '',
            description: task.description || '',
            has_deadline: !!task.hasDeadline,
            deadline_date: task.deadlineDate || null,
            deadline_time: task.deadlineTime || null,
            importance: task.importance || 'High',
            consequence: task.consequence || 'Big consequences',
            flexibility: task.flexibility || [],
            duration_minutes: typeof task.durationMinutes === 'number' ? task.durationMinutes : 60,
            duration_label: task.durationLabel || '1h',
            is_unknown_duration: !!task.isUnknownDuration,
            is_long_term: !!task.isLongTerm,
            priority_category: task.priorityCategory || 'DO_FIRST',
            execution_status: task.completed ? 'completed' : (task.isInProgress ? 'in_progress' : 'not_started'),
            completed: !!task.completed,
            is_in_progress: !!task.isInProgress,
            is_broken_down: !!(task.subtasks && task.subtasks.length > 0),
            already_know_what_to_do: !!task.alreadyKnowWhatToDo,
            updated_at: new Date().toISOString()
        };
    }

    function mapDbSubtaskToModel(dbSubtask) {
        if (!dbSubtask) return null;
        return {
            id: dbSubtask.id,
            taskId: dbSubtask.task_id,
            title: dbSubtask.title || '',
            durationMinutes: typeof dbSubtask.duration_minutes === 'number' ? dbSubtask.duration_minutes : null,
            position: typeof dbSubtask.position === 'number' ? dbSubtask.position : 0,
            completed: !!dbSubtask.completed
        };
    }

    function mapModelToDbSubtask(subtask, taskId, pos = 0) {
        return {
            id: subtask.id,
            task_id: taskId,
            title: subtask.title || '',
            duration_minutes: typeof subtask.durationMinutes === 'number' ? subtask.durationMinutes : null,
            position: typeof subtask.position === 'number' ? subtask.position : pos,
            completed: !!subtask.completed,
            updated_at: new Date().toISOString()
        };
    }

    // =========================================================================
    // LOCAL STORAGE CACHE HELPERS
    // =========================================================================

    function readLocal(key) {
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            console.warn("[TempoPlanStore] localStorage read error:", e);
            return null;
        }
    }

    function writeLocal(key, data) {
        try {
            if (data === null || data === undefined) {
                localStorage.removeItem(key);
            } else {
                localStorage.setItem(key, JSON.stringify(data));
            }
        } catch (e) {
            console.warn("[TempoPlanStore] localStorage write error:", e);
        }
    }

    // =========================================================================
    // INITIALIZATION & AUTH SYNC
    // =========================================================================

    async function init() {
        if (isInitialized) return;

        // Check if guest had an active plan or draft and migrate if user just logged in
        syncGuestToAuthenticated();

        // Preload active plan for current user if available
        const currentUserId = getUserId();
        const activeCached = readLocal(getActiveKey(currentUserId, 'emergency'));
        if (activeCached) {
            activePlans['emergency'] = activeCached;
        }

        const draftCached = readLocal(getDraftKey(currentUserId, 'emergency'));
        if (draftCached) {
            activeDrafts['emergency'] = draftCached;
        }

        isInitialized = true;
        console.log(`[TempoPlanStore] Initialized. Mode: ${isRemoteAvailable() ? 'Supabase Remote' : 'Local Fallback'}`);
    }

    function syncGuestToAuthenticated() {
        const userId = getUserId();
        if (userId === 'guest') return;

        const guestActive = readLocal(getActiveKey('guest', 'emergency'));
        const userActive = readLocal(getActiveKey(userId, 'emergency'));

        if (guestActive && !userActive) {
            writeLocal(getActiveKey(userId, 'emergency'), guestActive);
            writeLocal(getActiveKey('guest', 'emergency'), null);
            activePlans['emergency'] = guestActive;
            console.log("[TempoPlanStore] Migrated guest active plan to authenticated user.");
        }

        const guestDraft = readLocal(getDraftKey('guest', 'emergency'));
        const userDraft = readLocal(getDraftKey(userId, 'emergency'));

        if (guestDraft && !userDraft) {
            writeLocal(getDraftKey(userId, 'emergency'), guestDraft);
            writeLocal(getDraftKey('guest', 'emergency'), null);
            activeDrafts['emergency'] = guestDraft;
            console.log("[TempoPlanStore] Migrated guest draft to authenticated user.");
        }
    }

    // =========================================================================
    // DRAFT AUTOSAVE & RESTORATION
    // =========================================================================

    async function saveDraft(planType = 'emergency', draftData) {
        if (!draftData) return;
        const userId = getUserId();
        const key = getDraftKey(userId, planType);

        // Stamp save time
        const draftToStore = {
            ...draftData,
            planType,
            savedAt: Date.now()
        };

        // 1. Synchronous write to memory and local cache
        activeDrafts[planType] = draftToStore;
        writeLocal(key, draftToStore);

        // 2. If Supabase is available, asynchronously sync to DB
        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                // Upsert into public.plans table with status 'draft'
                await supabase.from('plans').upsert({
                    user_id: userId,
                    plan_type: planType,
                    status: 'draft',
                    title: `${planType === 'emergency' ? 'Emergency' : 'Action'} Plan (Draft)`,
                    metadata: draftToStore,
                    updated_at: new Date().toISOString()
                }, { onConflict: 'user_id, plan_type, status' }).select();
            } catch (err) {
                // Log warning and keep working with local cache
                console.warn("[TempoPlanStore] Remote draft autosave warning (local cache preserved):", err);
            }
        }
    }

    async function loadDraft(planType = 'emergency') {
        const userId = getUserId();
        const localDraft = activeDrafts[planType] || readLocal(getDraftKey(userId, planType));

        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                const { data, error } = await supabase
                    .from('plans')
                    .select('*')
                    .eq('user_id', userId)
                    .eq('plan_type', planType)
                    .eq('status', 'draft')
                    .order('updated_at', { ascending: false })
                    .limit(1);

                if (!error && data && data.length > 0 && data[0].metadata) {
                    const remoteDraft = data[0].metadata;
                    // If remote draft is newer or local is missing, use remote
                    if (!localDraft || !localDraft.savedAt || (new Date(data[0].updated_at).getTime() > localDraft.savedAt)) {
                        activeDrafts[planType] = remoteDraft;
                        writeLocal(getDraftKey(userId, planType), remoteDraft);
                        return remoteDraft;
                    }
                }
            } catch (err) {
                console.warn("[TempoPlanStore] Error loading remote draft, using local cache:", err);
            }
        }

        return localDraft || null;
    }

    async function clearDraft(planType = 'emergency') {
        const userId = getUserId();
        delete activeDrafts[planType];
        writeLocal(getDraftKey(userId, planType), null);

        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                await supabase
                    .from('plans')
                    .delete()
                    .eq('user_id', userId)
                    .eq('plan_type', planType)
                    .eq('status', 'draft');
            } catch (err) {
                console.warn("[TempoPlanStore] Error clearing remote draft:", err);
            }
        }
    }

    // =========================================================================
    // ACTIVE PLAN PERSISTENCE (SAVED / CONFIRMED PLAN)
    // =========================================================================

    async function saveActivePlan(planType = 'emergency', planData) {
        if (!planData) return null;
        const userId = getUserId();
        const activeKey = getActiveKey(userId, planType);

        // Ensure title & timestamps
        const fullPlan = {
            id: planData.id || `plan_${planType}_${Date.now()}`,
            planType,
            status: 'active',
            title: planData.title || 'Emergency Plan',
            totalPlannedMinutes: planData.totalPlannedMinutes || 0,
            plannedTasks: planData.plannedTasks || [],
            unallocatedTasks: planData.unallocatedTasks || [],
            availabilityDays: planData.availabilityDays || [],
            createdAt: planData.createdAt || new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };

        // 1. Immediately cache in memory and localStorage (zero latency)
        activePlans[planType] = fullPlan;
        writeLocal(activeKey, fullPlan);

        // 2. Clear any active draft since the plan is now finalized
        clearDraft(planType);

        // 3. Remote persistence in Supabase
        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                // A. Upsert Shared Tasks
                const allTasks = [];
                const allSubtasks = [];

                if (Array.isArray(fullPlan.plannedTasks)) {
                    fullPlan.plannedTasks.forEach(item => {
                        if (item && item.task) {
                            allTasks.push(item.task);
                            if (Array.isArray(item.task.subtasks)) {
                                item.task.subtasks.forEach((sub, sIdx) => {
                                    allSubtasks.push({ subtask: sub, taskId: item.task.id, position: sIdx });
                                });
                            }
                        }
                    });
                }

                if (Array.isArray(fullPlan.unallocatedTasks)) {
                    fullPlan.unallocatedTasks.forEach(task => {
                        if (task) allTasks.push(task);
                    });
                }

                // Upsert tasks
                if (allTasks.length > 0) {
                    const dbTasks = allTasks.map(t => mapModelToDbTask(t, userId));
                    await supabase.from('tasks').upsert(dbTasks, { onConflict: 'id' });
                }

                // Upsert subtasks
                if (allSubtasks.length > 0) {
                    const dbSubtasks = allSubtasks.map(item => mapModelToDbSubtask(item.subtask, item.taskId, item.position));
                    await supabase.from('subtasks').upsert(dbSubtasks, { onConflict: 'id' });
                }

                // B. Upsert Plan Record
                // First archive previous active plans of this type to maintain single active plan invariant
                await supabase
                    .from('plans')
                    .update({ status: 'archived', updated_at: new Date().toISOString() })
                    .eq('user_id', userId)
                    .eq('plan_type', planType)
                    .eq('status', 'active');

                // Insert the new active plan
                const { data: newPlanData, error: planError } = await supabase
                    .from('plans')
                    .insert({
                        user_id: userId,
                        plan_type: planType,
                        status: 'active',
                        title: fullPlan.title,
                        metadata: {
                            totalPlannedMinutes: fullPlan.totalPlannedMinutes,
                            unallocatedTasks: fullPlan.unallocatedTasks,
                            availabilityDays: fullPlan.availabilityDays
                        },
                        updated_at: new Date().toISOString()
                    })
                    .select()
                    .single();

                if (!planError && newPlanData) {
                    fullPlan.id = newPlanData.id;
                    activePlans[planType] = fullPlan;
                    writeLocal(activeKey, fullPlan);

                    // C. Insert Plan Items for ordering & scheduling
                    if (Array.isArray(fullPlan.plannedTasks) && fullPlan.plannedTasks.length > 0) {
                        const dbPlanItems = fullPlan.plannedTasks.map((item, index) => ({
                            plan_id: newPlanData.id,
                            task_id: item.task.id,
                            position: index,
                            scheduled_date: item.date || null,
                            scheduled_day_label: item.dayLabel || null,
                            scheduled_start: item.startTime || null,
                            scheduled_end: item.endTime || null,
                            start_minutes: item.startMinutes || null,
                            end_minutes: item.endMinutes || null,
                            execution_badge: item.executionBadge || (index === 0 ? 'UP NEXT' : (index === 1 ? 'THEN' : 'LATER')),
                            is_over_capacity: !!item.isOverCapacity,
                            has_deadline_conflict: !!item.hasDeadlineConflict,
                            updated_at: new Date().toISOString()
                        }));

                        await supabase.from('plan_items').insert(dbPlanItems);
                    }
                }
                console.log("[TempoPlanStore] Active plan saved successfully to Supabase & local cache.");
            } catch (err) {
                console.warn("[TempoPlanStore] Error persisting plan remotely (local cache intact):", err);
            }
        }

        return fullPlan;
    }

    async function loadActivePlan(planType = 'emergency') {
        const userId = getUserId();
        const localPlan = activePlans[planType] || readLocal(getActiveKey(userId, planType));

        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                const { data: planRows, error: planErr } = await supabase
                    .from('plans')
                    .select('*')
                    .eq('user_id', userId)
                    .eq('plan_type', planType)
                    .eq('status', 'active')
                    .order('updated_at', { ascending: false })
                    .limit(1);

                if (!planErr && planRows && planRows.length > 0) {
                    const planRow = planRows[0];

                    // Fetch plan items
                    const { data: itemRows } = await supabase
                        .from('plan_items')
                        .select('*')
                        .eq('plan_id', planRow.id)
                        .order('position', { ascending: true });

                    const taskIds = (itemRows || []).map(pi => pi.task_id);

                    // Fetch tasks
                    let taskMap = {};
                    if (taskIds.length > 0) {
                        const { data: taskRows } = await supabase
                            .from('tasks')
                            .select('*')
                            .in('id', taskIds);

                        // Fetch subtasks
                        const { data: subtaskRows } = await supabase
                            .from('subtasks')
                            .select('*')
                            .in('task_id', taskIds)
                            .order('position', { ascending: true });

                        const subtaskMap = {};
                        (subtaskRows || []).forEach(sub => {
                            if (!subtaskMap[sub.task_id]) subtaskMap[sub.task_id] = [];
                            subtaskMap[sub.task_id].push(sub);
                        });

                        (taskRows || []).forEach(t => {
                            taskMap[t.id] = mapDbTaskToModel(t, subtaskMap[t.id] || []);
                        });
                    }

                    // Reconstruct plannedTasks array in sequence
                    const plannedTasks = (itemRows || []).map(pi => {
                        const taskModel = taskMap[pi.task_id] || { id: pi.task_id, name: 'Untitled Task', subtasks: [] };
                        return {
                            task: taskModel,
                            date: pi.scheduled_date,
                            dayLabel: pi.scheduled_day_label,
                            startTime: pi.scheduled_start,
                            endTime: pi.scheduled_end,
                            startMinutes: pi.start_minutes,
                            endMinutes: pi.end_minutes,
                            executionBadge: pi.execution_badge || 'UP NEXT',
                            isOverCapacity: !!pi.is_over_capacity,
                            hasDeadlineConflict: !!pi.has_deadline_conflict
                        };
                    });

                    const remotePlan = {
                        id: planRow.id,
                        planType: planRow.plan_type,
                        status: 'active',
                        title: planRow.title,
                        totalPlannedMinutes: planRow.metadata?.totalPlannedMinutes || 0,
                        plannedTasks,
                        unallocatedTasks: planRow.metadata?.unallocatedTasks || [],
                        availabilityDays: planRow.metadata?.availabilityDays || [],
                        createdAt: planRow.created_at,
                        updatedAt: planRow.updated_at
                    };

                    activePlans[planType] = remotePlan;
                    writeLocal(getActiveKey(userId, planType), remotePlan);
                    return remotePlan;
                }
            } catch (err) {
                console.warn("[TempoPlanStore] Error querying remote active plan, falling back to local:", err);
            }
        }

        return localPlan || null;
    }

    async function archiveActivePlan(planType = 'emergency') {
        const userId = getUserId();
        const activeKey = getActiveKey(userId, planType);
        delete activePlans[planType];
        writeLocal(activeKey, null);

        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                await supabase
                    .from('plans')
                    .update({ status: 'archived', updated_at: new Date().toISOString() })
                    .eq('user_id', userId)
                    .eq('plan_type', planType)
                    .eq('status', 'active');
            } catch (err) {
                console.warn("[TempoPlanStore] Error archiving remote plan:", err);
            }
        }
    }

    function hasActivePlan(planType = 'emergency') {
        const userId = getUserId();
        return !!(activePlans[planType] || readLocal(getActiveKey(userId, planType)));
    }

    function hasDraft(planType = 'emergency') {
        const userId = getUserId();
        return !!(activeDrafts[planType] || readLocal(getDraftKey(userId, planType)));
    }

    // =========================================================================
    // MUTATION HELPERS FOR SHARED TASKS & SUBTASKS
    // =========================================================================

    async function updateTaskState(taskId, updates) {
        if (!taskId || !updates) return;
        const userId = getUserId();

        // 1. Update in-memory active plan(s)
        Object.keys(activePlans).forEach(pt => {
            const plan = activePlans[pt];
            if (plan && Array.isArray(plan.plannedTasks)) {
                const item = plan.plannedTasks.find(ptItem => ptItem.task && ptItem.task.id === taskId);
                if (item) {
                    Object.assign(item.task, updates);
                }
            }
            if (plan && Array.isArray(plan.unallocatedTasks)) {
                const task = plan.unallocatedTasks.find(t => t.id === taskId);
                if (task) {
                    Object.assign(task, updates);
                }
            }
            writeLocal(getActiveKey(userId, pt), plan);
        });

        // 2. Also update in draft if exists
        Object.keys(activeDrafts).forEach(pt => {
            const draft = activeDrafts[pt];
            if (draft && Array.isArray(draft.tasks)) {
                const draftTask = draft.tasks.find(t => t.id === taskId);
                if (draftTask) {
                    Object.assign(draftTask, updates);
                    writeLocal(getDraftKey(userId, pt), draft);
                }
            }
        });

        // 3. Remote update in Supabase
        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                const dbUpdates = {
                    updated_at: new Date().toISOString()
                };
                if ('completed' in updates) {
                    dbUpdates.completed = !!updates.completed;
                    dbUpdates.execution_status = updates.completed ? 'completed' : (updates.isInProgress ? 'in_progress' : 'not_started');
                }
                if ('isInProgress' in updates) {
                    dbUpdates.is_in_progress = !!updates.isInProgress;
                    if (!updates.completed) {
                        dbUpdates.execution_status = updates.isInProgress ? 'in_progress' : 'not_started';
                    }
                }
                if ('name' in updates) dbUpdates.name = updates.name;
                if ('durationMinutes' in updates) dbUpdates.duration_minutes = updates.durationMinutes;
                if ('durationLabel' in updates) dbUpdates.duration_label = updates.durationLabel;

                await supabase
                    .from('tasks')
                    .update(dbUpdates)
                    .eq('id', taskId);
            } catch (err) {
                console.warn("[TempoPlanStore] Remote task state update error:", err);
            }
        }
    }

    async function updateSubtaskState(taskId, subtaskId, updates) {
        if (!subtaskId || !updates) return;
        const userId = getUserId();

        // 1. Update in-memory active plan(s)
        Object.keys(activePlans).forEach(pt => {
            const plan = activePlans[pt];
            if (plan && Array.isArray(plan.plannedTasks)) {
                plan.plannedTasks.forEach(item => {
                    if (item.task && Array.isArray(item.task.subtasks)) {
                        const sub = item.task.subtasks.find(s => s.id === subtaskId);
                        if (sub) {
                            Object.assign(sub, updates);
                        }
                    }
                });
            }
            writeLocal(getActiveKey(userId, pt), plan);
        });

        // 2. Also update in draft
        Object.keys(activeDrafts).forEach(pt => {
            const draft = activeDrafts[pt];
            if (draft && Array.isArray(draft.tasks)) {
                draft.tasks.forEach(t => {
                    if (Array.isArray(t.subtasks)) {
                        const sub = t.subtasks.find(s => s.id === subtaskId);
                        if (sub) {
                            Object.assign(sub, updates);
                            writeLocal(getDraftKey(userId, pt), draft);
                        }
                    }
                });
            }
        });

        // 3. Remote update in Supabase
        if (isRemoteAvailable()) {
            const supabase = getSupabase();
            try {
                const dbUpdates = {
                    updated_at: new Date().toISOString()
                };
                if ('completed' in updates) dbUpdates.completed = !!updates.completed;
                if ('durationMinutes' in updates) dbUpdates.duration_minutes = updates.durationMinutes;
                if ('title' in updates) dbUpdates.title = updates.title;

                await supabase
                    .from('subtasks')
                    .update(dbUpdates)
                    .eq('id', subtaskId);
            } catch (err) {
                console.warn("[TempoPlanStore] Remote subtask state update error:", err);
            }
        }
    }

    // Public API
    return {
        init,
        isRemoteAvailable,
        getUserId,
        // Draft APIs
        saveDraft,
        loadDraft,
        clearDraft,
        hasDraft,
        // Active Plan APIs
        saveActivePlan,
        loadActivePlan,
        archiveActivePlan,
        hasActivePlan,
        // Entity Mutation APIs
        updateTaskState,
        updateSubtaskState
    };
})();
