// Sangrenes LMS Portal 2026 - Main JavaScript

// On page load: close all modals and ensure page is interactive
document.addEventListener('DOMContentLoaded', function() {
    // Close all modals on page load - remove all modal classes and inline styles
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active', 'show');
        modal.removeAttribute('style');
    });

    // Ensure body is scrollable
    document.body.style.overflow = '';
    document.body.style.pointerEvents = '';

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Toggle visibility for sessions/activities
async function toggleVisibility(type, id) {
    try {
        const response = await fetch('/api/toggle-visibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type, id: id })
        });
        const data = await response.json();
        if (data.success) {
            location.reload();
        } else {
            alert('Failed to update visibility');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
    }
}

// Bulk visibility update
async function bulkVisibility(activityId, makeVisible) {
    try {
        const response = await fetch('/api/bulk-visibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                activity_id: activityId,
                make_visible: makeVisible
            })
        });
        const data = await response.json();
        if (data.success) {
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Modal functions - using class-based approach for reliability
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Close any other open modals first
        document.querySelectorAll('.modal.active').forEach(m => {
            m.classList.remove('active');
        });
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close all modals
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = '';
}

// Close modal when clicking on the backdrop (outside modal content)
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal') && event.target.classList.contains('active')) {
        event.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeAllModals();
    }
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required]');
    let valid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#EF4444';
            valid = false;
        } else {
            input.style.borderColor = '#E5E7EB';
        }
    });

    return valid;
}

// Quiz timer
let quizTimer;
function startTimer(minutes, displayId) {
    let time = minutes * 60;
    const display = document.getElementById(displayId);

    quizTimer = setInterval(function() {
        const mins = Math.floor(time / 60);
        const secs = time % 60;

        display.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

        if (--time < 0) {
            clearInterval(quizTimer);
            document.getElementById('quizForm').submit();
        }
    }, 1000);
}

// Confirm delete
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this?');
}

// Grade input validation
document.querySelectorAll('.grade-input').forEach(input => {
    input.addEventListener('change', function() {
        const max = parseFloat(this.getAttribute('max'));
        const value = parseFloat(this.value);

        if (value > max) {
            alert(`Score cannot exceed ${max} points`);
            this.value = max;
        }
        if (value < 0) {
            this.value = 0;
        }
    });
});

// Add question dynamically
function addQuestionField() {
    const container = document.getElementById('questionsContainer');
    const count = container.children.length + 1;

    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-card';
    questionDiv.innerHTML = `
        <h4>Question ${count}</h4>
        <div class="form-group">
            <label>Question Text</label>
            <textarea name="questions[${count}][text]" required></textarea>
        </div>
        <div class="form-group">
            <label>Type</label>
            <select name="questions[${count}][type]" onchange="toggleOptions(this, ${count})">
                <option value="multiple_choice">Multiple Choice</option>
                <option value="true_false">True/False</option>
                <option value="short_answer">Short Answer</option>
            </select>
        </div>
        <div class="form-group" id="options-${count}">
            <label>Options (comma-separated)</label>
            <input type="text" name="questions[${count}][options]" placeholder="Option A, Option B, Option C, Option D">
        </div>
        <div class="form-group">
            <label>Correct Answer</label>
            <input type="text" name="questions[${count}][answer]" required>
        </div>
        <div class="form-group">
            <label>Points</label>
            <input type="number" name="questions[${count}][points]" value="1" min="1">
        </div>
    `;
    container.appendChild(questionDiv);
}

function toggleOptions(select, questionNum) {
    const optionsDiv = document.getElementById(`options-${questionNum}`);
    if (select.value === 'short_answer') {
        optionsDiv.style.display = 'none';
    } else if (select.value === 'true_false') {
        optionsDiv.innerHTML = '<label>Options</label><input type="text" name="questions[' + questionNum + '][options]" value="True, False" readonly>';
        optionsDiv.style.display = 'block';
    } else {
        optionsDiv.innerHTML = '<label>Options (comma-separated)</label><input type="text" name="questions[' + questionNum + '][options]" placeholder="Option A, Option B, Option C, Option D">';
        optionsDiv.style.display = 'block';
    }
}
