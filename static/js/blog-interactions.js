// Blog Interactions JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all blog interaction features
    initializeLikeButtons();
    initializeReplyForms();
    initializeInternalLinking();
});

function initializeLikeButtons() {
    // Comment like buttons
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const commentId = this.getAttribute('data-comment-id');
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateLikesCount(`likes-count-${commentId}`, data.likes_count);
                    toggleLikeButton(this, data.liked);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Post like button
    const postLikeBtn = document.querySelector('.like-post-btn');
    if (postLikeBtn) {
        postLikeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const postSlug = this.getAttribute('data-post-slug');
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateLikesCount('post-likes-count', data.likes_count, 'people liked this');
                    toggleLikeButton(this, data.liked, 'btn-outline-danger', 'btn-danger');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
}

function initializeReplyForms() {
    // All reply buttons and form interactions
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('reply-btn') || e.target.closest('.reply-btn')) {
            e.preventDefault();
            const button = e.target.classList.contains('reply-btn') ? e.target : e.target.closest('.reply-btn');
            const commentId = button.getAttribute('data-comment-id');
            showReplyForm(commentId, button.getAttribute('data-comment-name'));
        }

        if (e.target.classList.contains('cancel-reply') || e.target.closest('.cancel-reply')) {
            e.preventDefault();
            const button = e.target.classList.contains('cancel-reply') ? e.target : e.target.closest('.cancel-reply');
            const commentId = button.getAttribute('data-comment-id');
            hideReplyForm(commentId);
        }
    });
}

function showReplyForm(commentId, commentName) {
    // Hide all reply forms first
    document.querySelectorAll('.reply-form-container').forEach(form => {
        form.style.display = 'none';
    });
    // Show the specific reply form
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'block';
        // Update placeholder to reference the comment author
        const textarea = replyForm.querySelector('textarea[name="content"]');
        if (textarea) {
            textarea.placeholder = `Reply to ${commentName}...`;
            textarea.focus();
        }
    }
}

function hideReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'none';
        const textarea = replyForm.querySelector('textarea[name="content"]');
        if (textarea) {
            textarea.placeholder = 'Your reply...';
        }
    }
}

function updateLikesCount(elementId, count, suffix = 'likes') {
    const element = document.getElementById(elementId);
    if (element) {
        if (count > 0) {
            const countText = count === 1 ? '1 like' : `${count} ${suffix}`;
            element.textContent = countText;
        } else {
            element.textContent = '';
        }
    }
}

function toggleLikeButton(button, liked, defaultClass = 'btn-outline-primary', activeClass = 'btn-primary') {
    const heartIcon = button.querySelector('i');
    if (liked) {
        button.classList.remove(defaultClass);
        button.classList.add(activeClass);
        if (heartIcon) heartIcon.style.color = '#dc3545';
    } else {
        button.classList.remove(activeClass);
        button.classList.add(defaultClass);
        if (heartIcon) heartIcon.style.color = '';
    }
}

function getCsrfToken() {
    // Try to get CSRF token from various places
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenElement) {
        return tokenElement.value;
    }

    // Fallback: try to get from cookie
    const cookieValue = document.cookie.match(/(?:^|;) *csrftoken=([^;]*)(?:;|$)/);
    if (cookieValue) {
        return cookieValue[1];
    }

    return '';
}

// Helper function to show success messages
function showSuccessMessage(message) {
    // Check if the system messaging system is available
    if (typeof showSystemMessage === 'function') {
        showSystemMessage(message, 'success');
    } else {
        alert(message);
    }
}

// Internal Linking Autocomplete for Blog Posts
function initializeInternalLinking() {
    // Check if we're on a post creation/edit page with CKEditor
    const ckeditorElement = document.querySelector('.ckeditor-textarea');
    if (!ckeditorElement) return;

    // Wait for CKEditor to be initialized
    if (typeof CKEDITOR === 'undefined') return;

    // Wait a bit for CKEditor to load
    setTimeout(() => {
        const editor = CKEDITOR.instances[ckeditorElement.id];
        if (editor) {
            setupInternalLinkAutocomplete(editor);
        }
    }, 500);
}

function setupInternalLinkAutocomplete(editor) {
    let searchTimeout;
    let currentSuggestion = null;
    let currentLink = null;

    // Listen for key events in the editor
    editor.on('key', function(event) {
        // Only show suggestions when typing brackets or backslash for links
        const keyCode = event.data.keyCode;
        const ctrlPressed = event.data.ctrlKey || event.data.metaKey;

        if ((keyCode === 219 || keyCode === 220) || (ctrlPressed && keyCode === 75)) { // [ or ] or \ or Ctrl+K
            showInternalLinkDialog(editor);
        }
    });

    // Override the link button behavior
    editor.on('paste', function(event) {
        // Could intercept pasted URLs and suggest internal links
    });
}

function showInternalLinkDialog(editor) {
    // Get current selection
    const selection = editor.getSelection();
    const selectedText = selection && selection.getSelectedText();
    const range = selection && selection.getRanges()[0];

    // Create a simple dialog
    const dialogHtml = `
        <div id="internal-link-dialog" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 20px;
            width: 400px;
            max-width: 90vw;
            z-index: 9999;
        ">
            <h4 style="margin: 0 0 15px 0; color: #333;">Link to Existing Post</h4>
            <input type="text" id="internal-link-search" placeholder="Search for a post..." style="
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                margin-bottom: 10px;
                box-sizing: border-box;
            ">
            <div id="internal-link-results" style="
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #eee;
                border-radius: 4px;
                display: none;
            "></div>
            <div style="margin-top: 15px; text-align: right;">
                <button id="cancel-link" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    margin-right: 10px;
                    cursor: pointer;
                ">Cancel</button>
                <button id="insert-link" style="
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                " disabled>Insert Link</button>
            </div>
        </div>
        <div id="internal-link-overlay" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9998;
        "></div>
    `;

    document.body.insertAdjacentHTML('beforeend', dialogHtml);

    const dialog = document.getElementById('internal-link-dialog');
    const searchInput = document.getElementById('internal-link-search');
    const resultsDiv = document.getElementById('internal-link-results');
    const cancelBtn = document.getElementById('cancel-link');
    const insertBtn = document.getElementById('insert-link');
    const overlay = document.getElementById('internal-link-overlay');

    let searchTimeout;

    // Shared variable for selected post between functions
    let selectedPost = null;

    // Event listeners
    cancelBtn.addEventListener('click', closeDialog);
    overlay.addEventListener('click', closeDialog);

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchPosts(query, resultsDiv, insertBtn, selectedPost);
        }, 300);
    });

    insertBtn.addEventListener('click', function() {
        if (selectedPost) {
            const linkText = selectedPost.title;
            const linkUrl = selectedPost.url;

            // Insert the link into the editor
            editor.insertHtml(`<a href="${linkUrl}">${linkText}</a>`);
            closeDialog();
        }
    });

    searchInput.focus();

    function closeDialog() {
        dialog.remove();
        overlay.remove();
    }
}

function searchPosts(query, resultsDiv, insertBtn, selectedPost) {
    const searchUrl = '/blog/api/search-posts/?q=' + encodeURIComponent(query);

    fetch(searchUrl)
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = data.results.length > 0 ? 'block' : 'none';

            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div style="padding: 10px; color: #666;">No posts found</div>';
                insertBtn.disabled = true;
                return;
            }

            data.results.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.style.cssText = `
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                    cursor: pointer;
                    background: #f8f9fa;
                    transition: background-color 0.2s;
                `;

                postDiv.innerHTML = `
                    <div style="font-weight: bold; color: #007bff;">${post.title}</div>
                    <div style="font-size: 12px; color: #666;">
                        ${post.category} • ${post.date}
                    </div>
                `;

                postDiv.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#e3f2fd';
                });

                postDiv.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '#f8f9fa';
                });

                postDiv.addEventListener('click', function() {
                    // Remove selection from other items
                    resultsDiv.querySelectorAll('div').forEach(div => {
                        div.style.backgroundColor = '#f8f9fa';
                    });
                    this.style.backgroundColor = '#b3d9ff';

                    // Update button state
                    insertBtn.disabled = false;
                    insertBtn.textContent = `Insert Link: ${post.title}`;

                    // Store selected post in the parent scope variable
                    selectedPost = post;
                });

                resultsDiv.appendChild(postDiv);
            });

            insertBtn.disabled = true;
            insertBtn.textContent = 'Insert Link';
        })
        .catch(error => {
            console.error('Error searching posts:', error);
            resultsDiv.innerHTML = '<div style="padding: 10px; color: #d32f2f;">Error occurred during search</div>';
            resultsDiv.style.display = 'block';
            insertBtn.disabled = true;
        });
}
