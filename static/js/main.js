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
    
    document.getElementById('edit_subject_form').style.display = 'block';
}

// Populate reschedule form
function rescheduleSession(sessionId, currentDate) {
    document.getElementById('reschedule_session_id').value = sessionId;
    document.getElementById('reschedule_new_date').value = currentDate;
    
    document.getElementById('reschedule_form').style.display = 'block';
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
- 80-100%: Exam Ready ✓
- 60-79%: Making Progress
- 40-59%: Needs Work
- 0-39%: Not Ready

Your readiness score balances knowledge coverage (60%) with study consistency (40%).
    `;
    
    alert(explanation);
}
