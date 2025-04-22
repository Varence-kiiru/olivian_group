document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('newsletter-form');
    if (!form) return;
    
    const messageDiv = document.getElementById('newsletter-message');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        messageDiv.innerHTML = '<div class="alert alert-info">Processing your request...</div>';
        
        const email = form.querySelector('input[name="email"]').value;
        const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        fetch('/newsletter/signup/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `email=${encodeURIComponent(email)}`,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            const alertClass = data.status === 'success' ? 'success' : (data.status === 'info' ? 'info' : 'danger');
            messageDiv.innerHTML = `<div class="alert alert-${alertClass}">${data.message}</div>`;
            if (data.status === 'success') form.reset();
        })
        .catch(error => {
            console.error('Error:', error);
            messageDiv.innerHTML = '<div class="alert alert-danger">An error occurred. Please try again later.</div>';
        });
    });
});

$(document).ready(function() {
    function validateQuoteForm() {
        let isValid = true;
        $('.quote-form-error').remove();
        $('.is-invalid').removeClass('is-invalid');
        
        const fields = [
            { id: '#id_name', message: 'Please enter your name' },
            { id: '#id_email', message: 'Please enter your email address', regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
            { id: '#id_phone', message: 'Please enter your phone number' },
            { id: '#id_message', message: 'Please enter your message' }
        ];
        
        fields.forEach(field => {
            const input = $(field.id);
            if (!input.val().trim() || (field.regex && !field.regex.test(input.val().trim()))) {
                input.addClass('is-invalid');
                input.after(`<div class="invalid-feedback quote-form-error">${field.message}</div>`);
                isValid = false;
            }
        });
        
        return isValid;
    }

    $('#quoteForm').submit(function(e) {
        e.preventDefault();
        if (!validateQuoteForm()) return;
        
        $('#quoteSubmitBtn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...');
        $('#quoteSubmitBtn').prop('disabled', true);
        
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    $('#quoteFormContainer').html(
                        `<div class="alert alert-success"><h4 class="alert-heading">Thank You!</h4><p>${response.message}</p></div>`
                    );
                    $('#quoteForm')[0].reset();
                } else {
                    let errors = JSON.parse(response.errors);
                    $.each(errors, function(field, messages) {
                        let inputField = $(`#id_${field}`);
                        inputField.addClass('is-invalid');
                        messages.forEach(msg => {
                            inputField.after(`<div class="invalid-feedback quote-form-error">${msg.message}</div>`);
                        });
                    });
                    $('#quoteFormMessage').html('<div class="alert alert-danger quote-form-error">Please correct the errors below.</div>');
                }
            },
            error: function() {
                $('#quoteFormMessage').html('<div class="alert alert-danger quote-form-error">An error occurred. Please try again later.</div>');
            },
            complete: function() {
                $('#quoteSubmitBtn').html('Submit');
                $('#quoteSubmitBtn').prop('disabled', false);
            }
        });
    });

    $('#quoteForm input, #quoteForm textarea').on('input', function() {
        $(this).removeClass('is-invalid');
        $(this).next('.quote-form-error').remove();
    });
});
