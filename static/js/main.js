// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

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
