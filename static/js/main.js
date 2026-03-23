/**
 * Smart Study Planner - Main JavaScript
 */

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const buttons = this.querySelectorAll('button[type="submit"]');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.6';
                btn.style.cursor = 'not-allowed';
            });
        });
    });
});

// Slideout animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
`;
document.head.appendChild(style);

// Toggle topic completion (AJAX)
function toggleTopic(topicId) {
    fetch(`/topics/${topicId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to update statistics
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error toggling topic:', error);
    });
}

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this? This action cannot be undone.');
}

// Show/hide forms
function toggleForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}

// Populate edit form with subject data
function editSubject(id, name, examDate, difficulty, color) {
    document.getElementById('edit_subject_id').value = id;
    document.getElementById('edit_subject_name').value = name;
    document.getElementById('edit_exam_date').value = examDate;
    document.getElementById('edit_difficulty').value = difficulty;
    document.getElementById('edit_color').value = color;
    
    document.getElementById('edit_form_element').action = `/subjects/${id}/edit`;
    const form = document.getElementById('edit_subject_form');
    form.style.display = 'flex';
    form.classList.remove('hidden');
}

// Populate reschedule form
function rescheduleSession(sessionId, currentDate) {
    document.getElementById('reschedule_session_id').value = sessionId;
    document.getElementById('reschedule_new_date').value = currentDate;
    
    document.getElementById('reschedule_form_element').action = `/sessions/${sessionId}/reschedule`;
    const form = document.getElementById('reschedule_form');
    form.style.display = 'flex';
    form.classList.remove('hidden');
}

// Complete session with actual minutes
function completeSession(sessionId, plannedMinutes) {
    const actualMinutes = prompt(`How many minutes did you actually study?\n(Planned: ${plannedMinutes} minutes)`, plannedMinutes);
    
    if (actualMinutes !== null) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/sessions/${sessionId}/complete`;
        
        const minutesInput = document.createElement('input');
        minutesInput.type = 'hidden';
        minutesInput.name = 'actual_minutes';
        minutesInput.value = actualMinutes;
        
        form.appendChild(minutesInput);
        document.body.appendChild(form);
        form.submit();
    }
}

// Add note to session
function addNote(sessionId) {
    const note = prompt('Add a note to this session:');
    
    if (note !== null && note.trim() !== '') {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/sessions/${sessionId}/note`;
        
        const noteInput = document.createElement('input');
        noteInput.type = 'hidden';
        noteInput.name = 'notes';
        noteInput.value = note;
        
        form.appendChild(noteInput);
        document.body.appendChild(form);
        form.submit();
    }
}

// Form validation helpers
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--error-color)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--border-color)';
        }
    });
    
    return isValid;
}

// Clear form validation errors on input
document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            this.style.borderColor = 'var(--border-color)';
        });
    });
});

// Add multiple topics quickly
let topicCount = 1;

function addTopicRow() {
    const container = document.getElementById('topics_container');
    if (!container) return;
    
    topicCount++;
    
    const row = document.createElement('div');
    row.className = 'form-row';
    row.id = `topic_row_${topicCount}`;
    row.innerHTML = `
        <div class="form-group">
            <input type="text" name="topics[${topicCount}][title]" class="form-input" placeholder="Topic title" required>
        </div>
        <div class="form-group">
            <input type="number" name="topics[${topicCount}][minutes]" class="form-input" value="60" min="1" required>
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-danger btn-sm" onclick="removeTopicRow(${topicCount})">Remove</button>
        </div>
    `;
    
    container.appendChild(row);
}

function removeTopicRow(id) {
    const row = document.getElementById(`topic_row_${id}`);
    if (row) {
        row.remove();
    }
}

// Update progress bar animation
function animateProgressBar(elementId, targetPercentage) {
    const bar = document.getElementById(elementId);
    if (!bar) return;
    
    let current = 0;
    const increment = targetPercentage / 50;
    
    const interval = setInterval(() => {
        current += increment;
        if (current >= targetPercentage) {
            current = targetPercentage;
            clearInterval(interval);
        }
        bar.style.width = current + '%';
        bar.textContent = Math.round(current) + '%';
    }, 20);
}

// Initialize progress bars on page load
document.addEventListener('DOMContentLoaded', function() {
    const progressBars = document.querySelectorAll('.progress-bar-fill[data-percentage]');
    
    progressBars.forEach(bar => {
        const percentage = parseFloat(bar.dataset.percentage);
        setTimeout(() => {
            bar.style.width = percentage + '%';
        }, 100);
    });
});

// Print readiness explanation
function showReadinessExplanation() {
    const explanation = `
Readiness Score Calculation:

Formula: Readiness = (0.6 × Syllabus Completion %) + (0.4 × Consistency Score)

Where:
- Syllabus Completion % = (completed topic minutes / total topic minutes) × 100
- Consistency Score = (study streak / plan duration) × 100, capped at 100%

Interpretation:
- 80-100%: Exam Ready
- 60-79%: Making Progress
- 40-59%: Needs Work
- 0-39%: Not Ready

Your readiness score balances knowledge coverage (60%) with study consistency (40%).
    `;
    
    alert(explanation);
}


function toggleMobileNav() {
    const shell = document.getElementById('nav_shell');
    if (shell) shell.classList.toggle('open');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

document.addEventListener('click', function(event) {
    const modal = document.querySelector('.modal-shell:not(.hidden)');
    if (modal && event.target === modal) {
        modal.classList.add('hidden');
    }
});

window.addEventListener('DOMContentLoaded', function() {
    const minutesInput = document.getElementById('daily_study_minutes');
    const sessionsInput = document.getElementById('max_sessions_per_day');
    const minutesPreview = document.getElementById('study_minutes_preview');
    const sessionPreview = document.getElementById('session_size_preview');
    const blocksPreview = document.getElementById('blocks_preview');
    const selectedBlocks = document.querySelectorAll('input[name="blocks"]');
    const colorInput = document.getElementById('color');
    const colorText = document.getElementById('color-text');

    const refreshPreview = () => {
        if (minutesInput && sessionsInput && minutesPreview && sessionPreview) {
            const minutes = parseInt(minutesInput.value || '0', 10) || 0;
            const sessions = parseInt(sessionsInput.value || '1', 10) || 1;
            minutesPreview.textContent = `${minutes} min`;
            sessionPreview.textContent = `${Math.max(30, Math.ceil(minutes / sessions))} min each`;
        }

        if (blocksPreview) {
            const labels = Array.from(document.querySelectorAll('input[name="blocks"]:checked')).map(input => input.value);
            blocksPreview.textContent = labels.length ? labels.join(' / ') : 'Choose at least one';
        }
    };

    refreshPreview();
    if (minutesInput) minutesInput.addEventListener('input', refreshPreview);
    if (sessionsInput) sessionsInput.addEventListener('change', refreshPreview);
    selectedBlocks.forEach(input => input.addEventListener('change', refreshPreview));
    if (colorInput && colorText) {
        const updateColor = () => colorText.textContent = colorInput.value.toUpperCase();
        updateColor();
        colorInput.addEventListener('input', updateColor);
    }
});


function openCompleteModal(sessionId, plannedMinutes, title) {
    const modal = document.getElementById('complete_session_modal');
    const form = document.getElementById('complete_session_form');
    const heading = document.getElementById('complete_session_heading');
    const minutesInput = document.getElementById('actual_minutes');
    const notesInput = document.getElementById('session_notes');
    if (!modal || !form || !heading || !minutesInput) return;

    form.action = `/sessions/${sessionId}/complete`;
    heading.textContent = `${title} planned ${plannedMinutes} min`;
    minutesInput.value = plannedMinutes;
    if (notesInput) notesInput.value = '';
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
}


async function postSessionAction(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
    });
    if (!response.ok) throw new Error('Request failed');
    return response.json();
}

function applyDashboardMetrics(data) {
    const progress = document.getElementById('metric_progress');
    const streak = document.getElementById('metric_streak');
    const minutes = document.getElementById('metric_minutes');
    if (progress) progress.textContent = `${data.progress_percentage}%`;
    if (streak) streak.textContent = `${data.streak} days`;
    if (minutes) minutes.textContent = `${data.today_minutes} min`;
}

async function completeSessionInline(sessionId, plannedMinutes, title) {
    const card = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (!card) return openCompleteModal(sessionId, plannedMinutes, title);

    const formData = new FormData();
    formData.append('actual_minutes', plannedMinutes);
    formData.append('notes', 'Completed from timeline');
    card.classList.add('is-completing');

    try {
        const data = await postSessionAction(`/sessions/${sessionId}/complete`, formData);
        const pill = card.querySelector('.js-status-pill');
        if (pill) {
            pill.textContent = 'Done';
            pill.className = 'status-pill status-completed js-status-pill';
        }
        const actions = card.querySelector('.session-actions');
        if (actions) actions.remove();
        card.classList.remove('is-completing');
        card.classList.add('is-done');
        applyDashboardMetrics(data);
    } catch (error) {
        card.classList.remove('is-completing');
        openCompleteModal(sessionId, plannedMinutes, title);
    }
}

async function skipSessionInline(sessionId) {
    const card = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (!card) return;
    const formData = new FormData();
    card.classList.add('is-completing');
    try {
        const data = await postSessionAction(`/sessions/${sessionId}/skip`, formData);
        const pill = card.querySelector('.js-status-pill');
        if (pill) {
            pill.textContent = 'Skipped';
            pill.className = 'status-pill status-skipped js-status-pill';
        }
        const actions = card.querySelector('.session-actions');
        if (actions) actions.remove();
        card.classList.remove('is-completing');
        applyDashboardMetrics(data);
    } catch (error) {
        card.classList.remove('is-completing');
        location.reload();
    }
}
