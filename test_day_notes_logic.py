# -*- coding: utf-8 -*-
import json

# Test JavaScript logic directly in Node or Python
test_js = """
function getLocalDateStr(d) {
    if (!d) return '';
    try {
        const dateObj = (typeof d === 'string' && d.length === 10 && d.includes('-')) ? null : new Date(d);
        if (dateObj && !isNaN(dateObj.getTime())) {
            const y = dateObj.getFullYear();
            const m = String(dateObj.getMonth() + 1).padStart(2, '0');
            const day = String(dateObj.getDate()).padStart(2, '0');
            return `${y}-${m}-${day}`;
        }
    } catch(e) {}
    if (typeof d === 'string' && d.includes('T')) {
        return d.split('T')[0];
    }
    return String(d).substring(0, 10);
}

function getUmodeDayNotesForToday(todayStr, storageMock, uid) {
    const targetDate = todayStr || getLocalDateStr(new Date());
    const dayNotes = [];
    const seenIds = new Set();

    function matchesToday(itemDate, createdAt, updatedAt) {
        if (itemDate && String(itemDate).substring(0, 10) === targetDate) return true;
        if (createdAt && getLocalDateStr(createdAt) === targetDate) return true;
        if (updatedAt && getLocalDateStr(updatedAt) === targetDate) return true;
        return false;
    }

    // 1. From tool notes
    try {
        const rawTool = storageMock[`tempo_tool_notes_${uid}`] || storageMock['tempo_tool_notes'];
        if (rawTool) {
            const all = JSON.parse(rawTool);
            if (Array.isArray(all)) {
                all.forEach(n => {
                    // Strictly exclude Task Notes
                    const isTaskNote = !!(n.taskId || n.category === 'task' || n.type === 'task');
                    if (isTaskNote) return;

                    if (matchesToday(n.date, n.createdAt, n.updatedAt)) {
                        const txt = (n.text || n.content || '').trim();
                        const key = n.id || txt;
                        if (txt && !seenIds.has(key)) {
                            seenIds.add(key);
                            dayNotes.push({
                                id: n.id || ('day_' + Math.random().toString(36).substr(2, 6)),
                                text: txt,
                                time: n.updatedAt || n.createdAt || targetDate,
                                type: 'day'
                            });
                        }
                    }
                });
            }
        }
    } catch (e) {}

    // 2. From tempo_day_notes
    try {
        const rawDay = storageMock[`tempo_day_notes_${uid}`] || storageMock['tempo_day_notes'];
        if (rawDay) {
            const all = JSON.parse(rawDay);
            if (Array.isArray(all)) {
                all.forEach(n => {
                    const isTaskNote = !!(n.taskId || n.category === 'task' || n.type === 'task');
                    if (isTaskNote) return;

                    if (matchesToday(n.date, n.createdAt, n.updatedAt)) {
                        const txt = (n.text || n.content || '').trim();
                        const key = n.id || txt;
                        if (txt && !seenIds.has(key)) {
                            seenIds.add(key);
                            dayNotes.push({
                                id: n.id || ('day_' + Math.random().toString(36).substr(2, 6)),
                                text: txt,
                                time: n.updatedAt || n.createdAt || targetDate,
                                type: 'day'
                            });
                        }
                    }
                });
            }
        }
    } catch (e) {}

    // 3. From self-check checkins
    try {
        const rawChk = storageMock[`tempo_selfcheck_checkins_${uid}`] || storageMock['tempo_selfcheck_checkins'];
        if (rawChk) {
            const checkins = JSON.parse(rawChk);
            if (Array.isArray(checkins)) {
                const todayChk = checkins.find(c => c.checkin_date === targetDate);
                if (todayChk && todayChk.overall_note && todayChk.overall_note.trim()) {
                    const txt = todayChk.overall_note.trim();
                    const key = 'chk_' + targetDate;
                    if (!seenIds.has(key) && !seenIds.has(txt)) {
                        seenIds.add(key);
                        seenIds.add(txt);
                        dayNotes.push({
                            id: key,
                            text: txt,
                            time: todayChk.updated_at || todayChk.completed_at || todayChk.created_at || targetDate,
                            type: 'day'
                        });
                    }
                }
            }
        }
    } catch (e) {}

    return dayNotes;
}

// RUN TESTS
const todayStr = '2026-10-28';
const uid = 'user_123';

const mock = {
    [`tempo_tool_notes_${uid}`]: JSON.stringify([
        { id: 'tn_1', taskId: 'task_bio', taskName: 'Bio chapter 6', text: 'Task note for bio', category: 'task', createdAt: '2026-10-28T10:00:00Z' },
        { id: 'dn_1', type: 'day', category: 'day', date: '2026-10-28', text: 'Remember to hydrate throughout exam prep', createdAt: '2026-10-28T09:00:00Z' },
        { id: 'dn_yesterday', type: 'day', category: 'day', date: '2026-10-27', text: 'Yesterday note', createdAt: '2026-10-27T09:00:00Z' },
        { id: 'dn_tomorrow', type: 'day', category: 'day', date: '2026-10-29', text: 'Tomorrow note', createdAt: '2026-10-29T09:00:00Z' }
    ]),
    [`tempo_day_notes_${uid}`]: JSON.stringify([
        { id: 'dn_2', date: '2026-10-28', text: 'Take a 10 min walk before evening study', createdAt: '2026-10-28T14:30:00Z' },
        { id: 'tn_accidental_task', taskId: 'task_chem', text: 'Should not appear', category: 'task', date: '2026-10-28' }
    ]),
    [`tempo_selfcheck_checkins_${uid}`]: JSON.stringify([
        { checkin_date: '2026-10-28', overall_note: 'Feeling better after afternoon break.' },
        { checkin_date: '2026-10-27', overall_note: 'Yesterday checkin note' }
    ])
};

const results = getUmodeDayNotesForToday(todayStr, mock, uid);
console.log(JSON.stringify(results, null, 2));
"""

import subprocess
res = subprocess.run(['node', '-e', test_js], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
