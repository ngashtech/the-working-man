
$(document).ready(function() {
    
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        $('.flash-messages-container .alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
    
    // Add padding to body for fixed navbar
    $('body').css('padding-top', '70px');
    
    // Active nav link highlighting based on current URL
    var currentPath = window.location.pathname;
    $('.navbar-nav a').each(function() {
        var href = $(this).attr('href');
        if (href && href === currentPath) {
            $(this).parent().addClass('active');
        }
    });
    
    // Initialize Bootstrap tooltips
    if (typeof $.fn.tooltip === 'function') {
        $('[data-toggle="tooltip"]').tooltip();
    }
    
    // Initialize Bootstrap popovers
    if (typeof $.fn.popover === 'function') {
        $('[data-toggle="popover"]').popover();
    }
    
    // Smooth scroll for anchor links
    $('a[href*="#"]:not([href="#"])').on('click', function() {
        var target = $(this.hash);
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
            return false;
        }
    });
    
    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Confirm close actions
    $('.confirm-close').on('click', function(e) {
        if (!confirm('Are you sure you want to close this job posting?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Toggle password visibility
    $('.password-toggle').on('click', function() {
        var passwordField = $($(this).data('target'));
        var icon = $(this).find('i');
        
        if (passwordField.attr('type') === 'password') {
            passwordField.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            passwordField.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // Character counters
    $('[data-max-chars]').each(function() {
        var maxChars = $(this).data('max-chars');
        var counterEl = $($(this).data('counter'));
        
        $(this).on('input', function() {
            var remaining = maxChars - $(this).val().length;
            if (counterEl.length) {
                counterEl.text(remaining);
                counterEl.css('color', remaining < 50 ? '#dd4b39' : '#999');
            }
        });
    });

    console.log('The Working Man Platform - Ready');
});

// Close flash message on button click
$(document).on('click', '.flash-messages-container .close', function() {
    $(this).closest('.alert').fadeOut('slow', function() {
        $(this).remove();
    });
});

// Dismiss alert on click
$(document).on('click', '.alert-dismissible', function() {
    $(this).fadeOut('slow', function() {
        $(this).remove();
    });
});

/**
 * Show a temporary notification message
 * @param {string} message - The message to display
 * @param {string} type - success, error, warning, info
 */
function showNotification(message, type) {
    var icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'danger': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    var alertClass = 'alert-' + (type || 'info');
    var iconClass = icons[type] || 'fa-info-circle';
    
    var alertHtml = 
        '<div class="alert ' + alertClass + ' alert-dismissible fade in" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">&times;</span></button>' +
        '<i class="fa ' + iconClass + '"></i> ' + message +
        '</div>';
    
    var container = $('.flash-messages-container');
    if (container.length === 0) {
        container = $('<div class="flash-messages-container"></div>');
        $('body').append(container);
    }
    
    container.append(alertHtml);
    
    setTimeout(function() {
        container.find('.alert').last().fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

/**
 * Format a date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    var date = new Date(dateString);
    var options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format a number as currency
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

/**
 * Truncate text to a maximum length
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
    maxLength = maxLength || 50;
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Get a URL parameter by name
 * @param {string} name - Parameter name
 * @returns {string} Parameter value
 */
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

/**
 * Generic AJAX POST request
 * @param {string} url - The URL to post to
 * @param {object} data - The data to send
 * @param {function} successCallback - Success callback
 * @param {function} errorCallback - Error callback
 */
function ajaxPost(url, data, successCallback, errorCallback) {
    $.ajax({
        url: url,
        type: 'POST',
        data: data,
        success: function(response) {
            if (response.success && successCallback) {
                successCallback(response);
            } else if (!response.success && errorCallback) {
                errorCallback(response);
            } else if (response.message) {
                showNotification(response.message, response.success ? 'success' : 'error');
            }
        },
        error: function(xhr) {
            var message = 'An error occurred. Please try again.';
            try {
                var response = JSON.parse(xhr.responseText);
                message = response.message || message;
            } catch(e) {}
            showNotification(message, 'error');
            if (errorCallback) errorCallback({success: false, message: message});
        }
    });
}

/**
 * Generic AJAX GET request
 * @param {string} url - The URL to fetch
 * @param {function} successCallback - Success callback
 * @param {function} errorCallback - Error callback
 */
function ajaxGet(url, successCallback, errorCallback) {
    $.ajax({
        url: url,
        type: 'GET',
        success: function(response) {
            if (successCallback) successCallback(response);
        },
        error: function(xhr) {
            var message = 'Failed to load data.';
            try {
                var response = JSON.parse(xhr.responseText);
                message = response.message || message;
            } catch(e) {}
            showNotification(message, 'error');
            if (errorCallback) errorCallback({success: false, message: message});
        }
    });
}

/**
 * Serialize a form to a JSON object
 * @param {Element} formElement - The form element
 * @returns {object} Form data as JSON
 */
function formToJSON(formElement) {
    var formData = {};
    $(formElement).find('input, select, textarea').each(function() {
        var name = $(this).attr('name');
        var value = $(this).val();
        if (name) {
            if ($(this).attr('type') === 'checkbox') {
                if (!formData[name]) formData[name] = [];
                if ($(this).is(':checked')) formData[name].push(value);
            } else if ($(this).attr('type') === 'radio') {
                if ($(this).is(':checked')) formData[name] = value;
            } else {
                formData[name] = value;
            }
        }
    });
    return formData;
}

/**
 * Validate required fields in a form
 * @param {Element} formElement - The form element
 * @returns {boolean} Whether the form is valid
 */
function validateForm(formElement) {
    var isValid = true;
    $(formElement).find('[required]').each(function() {
        if (!$(this).val()) {
            $(this).css('border-color', '#dd4b39');
            isValid = false;
        } else {
            $(this).css('border-color', '#e0e0e0');
        }
    });
    return isValid;
}     



// ==================== API HELPER FUNCTIONS ====================

/**
 * Base API URL
 */
var API_BASE = '';

/**
 * Generic API GET request
 */
function apiGet(endpoint, params, callback) {
    var url = API_BASE + endpoint;
    if (params) {
        var queryString = Object.keys(params)
            .filter(function(key) { return params[key] !== '' && params[key] !== null && params[key] !== undefined; })
            .map(function(key) { return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]); })
            .join('&');
        if (queryString) url += '?' + queryString;
    }
    
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            if (callback) callback(response);
        },
        error: function(xhr, status, error) {
            console.error('API Error:', endpoint, error);
            if (callback) callback({ success: false, error: error });
        }
    });
}

/**
 * Generic API POST request
 */
function apiPost(endpoint, data, callback) {
    $.ajax({
        url: API_BASE + endpoint,
        type: 'POST',
        data: JSON.stringify(data),
        contentType: 'application/json',
        dataType: 'json',
        success: function(response) {
            if (callback) callback(response);
        },
        error: function(xhr, status, error) {
            console.error('API Error:', endpoint, error);
            if (callback) callback({ success: false, error: error });
        }
    });
}

/**
 * Load available jobs from API
 */
function loadJobsFromAPI(params, containerId, emptyMessage) {
    var container = $('#' + (containerId || 'jobsList'));
    var originalHtml = container.html();
    container.html('<div class="text-center" style="padding:40px;"><i class="fa fa-spinner fa-spin fa-3x" style="color:#3c8dbc;"></i><p>Loading jobs...</p></div>');
    
    apiGet('/api/jobs', params, function(response) {
        if (response.success && response.jobs && response.jobs.length > 0) {
            renderJobCards(response.jobs, container);
        } else {
            container.html('<div class="empty-state"><i class="fa fa-search"></i><h4>' + (emptyMessage || 'No jobs found') + '</h4></div>');
        }
    });
}

/**
 * Load available workers from API
 */
function loadWorkersFromAPI(params, containerId, emptyMessage) {
    var container = $('#' + (containerId || 'workersList'));
    container.html('<div class="text-center" style="padding:40px;"><i class="fa fa-spinner fa-spin fa-3x" style="color:#3c8dbc;"></i><p>Loading workers...</p></div>');
    
    apiGet('/api/workers', params, function(response) {
        if (response.success && response.workers && response.workers.length > 0) {
            renderWorkerCards(response.workers, container);
        } else {
            container.html('<div class="empty-state"><i class="fa fa-users"></i><h4>' + (emptyMessage || 'No workers found') + '</h4></div>');
        }
    });
}

/**
 * Load worker dashboard data
 */
function loadWorkerDashboard() {
    apiGet('/api/worker/dashboard', null, function(response) {
        if (response.success) {
            // Update stats
            $('#completedJobs').text(response.stats.completed_jobs || '0');
            $('#pendingApps').text(response.stats.pending_applications || '0');
            $('#activeMatches').text(response.stats.active_matches || '0');
            $('#workerRating').text((response.stats.rating || '0') + '/5');
            
            // Update profile completion
            var completion = response.stats.profile_completion || 0;
            $('#profileCompletionBar').css('width', completion + '%');
            $('#profileCompletionText').text(completion + '% Complete');
            
            // Show/hide completion alert
            if (completion < 100) {
                $('#profileCompletionAlert').show();
            } else {
                $('#profileCompletionAlert').hide();
            }
            
            // Load available jobs
            if (response.available_jobs && response.available_jobs.length > 0) {
                renderDashboardJobs(response.available_jobs);
            }
            
            // Load recent applications
            if (response.recent_applications && response.recent_applications.length > 0) {
                renderRecentApplications(response.recent_applications);
            }
        }
    });
}

/**
 * Load employer dashboard data
 */
function loadEmployerDashboard() {
    apiGet('/api/employer/dashboard', null, function(response) {
        if (response.success) {
            // Update stats
            $('#activeJobs').text(response.stats.active_jobs || '0');
            $('#totalJobs').text(response.stats.total_jobs || '0');
            $('#totalApplications').text(response.stats.total_applications || '0');
            $('#totalHired').text(response.stats.total_hired || '0');
            
            // Load recent jobs
            if (response.recent_jobs && response.recent_jobs.length > 0) {
                renderDashboardJobsEmployer(response.recent_jobs);
            }
            
            // Load available workers
            if (response.available_workers && response.available_workers.length > 0) {
                renderDashboardWorkers(response.available_workers);
            }
        }
    });
}

/**
 * Load notifications
 */
function loadNotifications() {
    apiGet('/api/notifications', { unread: 'false' }, function(response) {
        if (response.success) {
            renderNotifications(response.notifications);
            // Update badge
            if (response.unread_count > 0) {
                $('.notification-badge').text(response.unread_count).show();
            } else {
                $('.notification-badge').hide();
            }
        }
    });
}



// ==================== POST JOB (EMPLOYER ONLY) ====================
function showPostJobModal() {
    if (!currentUser) {
        showFlash('Please login as an employer to post jobs.', 'warning');
        showPage('login');
        return;
    }
    if (currentUser.role !== 'employer') {
        showFlash('Only employers can post jobs. Please register as an employer.', 'error');
        return;
    }
    $('#postJobModal').modal('show');
}

// Character counter for job description
$('#jobDescription').on('input', function() {
    $('#jobDescCount').text($(this).val().length);
});

function submitJob(e) {
    e.preventDefault();
    
    if (!currentUser || currentUser.role !== 'employer') {
        showFlash('You must be logged in as an employer to post jobs.', 'error');
        $('#postJobModal').modal('hide');
        return;
    }
    
    var data = {
        title: $('#jobTitle').val().trim(),
        description: $('#jobDescription').val().trim(),
        service_type_needed: $('#jobService').val(),
        location_name: $('#jobLocation').val().trim(),
        offered_pay_rate: $('#jobPay').val(),
        pay_period: $('#jobPayPeriod').val()
    };
    
    if (!data.title || !data.description || !data.service_type_needed || !data.location_name || !data.offered_pay_rate) {
        showFlash('Please fill all required fields.', 'error');
        return;
    }
    
    $.ajax({
        url: '/job/create',
        type: 'POST',
        data: data,
        dataType: 'json',
        success: function(r) {
            if (r && r.success) {
                $('#postJobModal').modal('hide');
                $('#postJobForm')[0].reset();
                showFlash('Job posted successfully! Workers can now see and apply for it.', 'success');
                loadJobs(); // Refresh jobs list
                loadHomeData(); // Refresh home data
            } else {
                showFlash(r ? r.message : 'Failed to post job.', 'error');
            }
        },
        error: function() {
            showFlash('Network error. Please try again.', 'error');
        }
    });
}

// ==================== CONTACT WORKER (AUTHENTICATED USERS ONLY) ====================
function contactWorker(userId, workerName) {
    if (!currentUser) {
        showFlash('Please login to contact workers.', 'warning');
        showPage('login');
        return;
    }
    
    $('#msgReceiverId').val(userId);
    $('#msgReceiverName').text(workerName || 'Worker');
    $('#msgContent').val('');
    $('#messageModal').modal('show');
    loadMessages(userId);
}

function loadMessages(userId) {
    $('#msgHistory').html('<p class="text-muted text-center">Loading...</p>');
    
    $.getJSON('/api/messages/' + userId, function(r) {
        if (r && r.success && r.messages && r.messages.length > 0) {
            var html = '';
            r.messages.forEach(function(m) {
                var align = m.is_mine ? 'right' : 'left';
                var bg = m.is_mine ? '#d4edda' : '#f0f0f0';
                html += '<div style="text-align:' + align + '; margin-bottom:8px;">' +
                    '<div style="display:inline-block; background:' + bg + '; padding:8px 12px; border-radius:10px; max-width:80%; text-align:left;">' +
                    '<small style="color:#999;">' + (m.is_mine ? 'You' : (r.other_user ? r.other_user.full_name : 'Them')) + '</small><br>' +
                    escapeHtml(m.content) +
                    '<br><small style="color:#aaa;">' + (m.created_at || '') + '</small>' +
                    '</div></div>';
            });
            $('#msgHistory').html(html);
            $('#msgHistory').scrollTop($('#msgHistory')[0].scrollHeight);
        } else {
            $('#msgHistory').html('<p class="text-muted text-center">No messages yet. Start the conversation!</p>');
        }
    });
}

function sendMessage(e) {
    e.preventDefault();
    
    if (!currentUser) {
        showFlash('Please login first.', 'error');
        return;
    }
    
    var receiverId = $('#msgReceiverId').val();
    var content = $('#msgContent').val().trim();
    
    if (!content) return;
    
    $.ajax({
        url: '/api/messages/send',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ receiver_id: parseInt(receiverId), content: content }),
        dataType: 'json',
        success: function(r) {
            if (r && r.success) {
                $('#msgContent').val('');
                loadMessages(receiverId);
            } else {
                showFlash('Failed to send message.', 'error');
            }
        },
        error: function() {
            showFlash('Network error.', 'error');
        }
    });
}

// ==================== REVIEW SYSTEM (EMPLOYER ONLY, AFTER JOB COMPLETION) ====================
function showReviewModal(matchId, workerName, jobTitle) {
    if (!currentUser) {
        showFlash('Please login to submit a review.', 'warning');
        showPage('login');
        return;
    }
    if (currentUser.role !== 'employer') {
        showFlash('Only employers can submit reviews.', 'error');
        return;
    }
    
    $('#reviewMatchId').val(matchId);
    $('#reviewWorkerName').text(workerName || 'Worker');
    $('#reviewJobTitle').text(jobTitle || 'Job');
    $('#reviewRating').val(0);
    $('#reviewComment').val('');
    $('#ratingText').text('Click to rate');
    resetStars();
    $('#reviewModal').modal('show');
}

var selectedRating = 0;

function highlightStars(rating) {
    $('#starRating i').each(function() {
        var r = parseInt($(this).data('rating'));
        if (r <= rating) {
            $(this).removeClass('fa-star-o').addClass('fa-star').css('color', '#f39c12');
        } else {
            $(this).removeClass('fa-star').addClass('fa-star-o').css('color', '#ddd');
        }
    });
}

function resetStars() {
    $('#starRating i').each(function() {
        var r = parseInt($(this).data('rating'));
        if (r <= selectedRating) {
            $(this).removeClass('fa-star-o').addClass('fa-star').css('color', '#f39c12');
        } else {
            $(this).removeClass('fa-star').addClass('fa-star-o').css('color', '#ddd');
        }
    });
}

function setRating(rating) {
    selectedRating = rating;
    $('#reviewRating').val(rating);
    resetStars();
    var texts = ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent!'];
    $('#ratingText').text(texts[rating] || '');
}

function submitReview(e) {
    e.preventDefault();
    
    if (!currentUser || currentUser.role !== 'employer') {
        showFlash('You must be logged in as an employer to submit reviews.', 'error');
        return;
    }
    
    var matchId = $('#reviewMatchId').val();
    var rating = parseInt($('#reviewRating').val());
    var comment = $('#reviewComment').val().trim();
    
    if (rating < 1 || rating > 5) {
        showFlash('Please select a rating (click the stars).', 'error');
        return;
    }
    
    $.ajax({
        url: '/review/create/' + matchId,
        type: 'POST',
        data: { rating: rating, comment: comment },
        dataType: 'json',
        success: function(r) {
            if (r && r.success) {
                $('#reviewModal').modal('hide');
                showFlash('Review submitted! Thank you for your feedback.', 'success');
                loadWorkers(); // Refresh worker list with new ratings
            } else {
                showFlash(r ? r.message : 'Failed to submit review.', 'error');
            }
        },
        error: function() {
            showFlash('Network error.', 'error');
        }
    });
}

// ==================== UPDATE DASHBOARD ====================
function loadDashboard() {
    if (!currentUser) { showPage('login'); return; }
    
    $('#dashWelcome').html('Welcome, <strong>' + currentUser.full_name + '</strong> (' + currentUser.role + ')');
    
    var actionsHtml = '';
    if (currentUser.role === 'worker') {
        actionsHtml = '<button class="btn btn-success btn-sm" onclick="showPage(\'jobs\')"><i class="fa fa-search"></i> Find Jobs</button> ';
        actionsHtml += '<button class="btn btn-info btn-sm" onclick="showPage(\'workers\')"><i class="fa fa-users"></i> Browse Workers</button>';
    } else if (currentUser.role === 'employer') {
        actionsHtml = '<button class="btn btn-success btn-lg btn-block" onclick="showPostJobModal()"><i class="fa fa-plus-circle"></i> <strong>Post a New Job</strong></button><br>';
        actionsHtml += '<button class="btn btn-info btn-sm" onclick="showPage(\'workers\')"><i class="fa fa-users"></i> Find Workers</button> ';
        actionsHtml += '<button class="btn btn-primary btn-sm" onclick="showPage(\'jobs\')"><i class="fa fa-list"></i> My Jobs</button>';
    }
    $('#dashActions').html(actionsHtml);
}

// ==================== HELPER ====================
function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}



/**
 * Load conversations
 */
function loadConversations() {
    apiGet('/api/messages', null, function(response) {
        if (response.success && response.conversations) {
            renderConversations(response.conversations);
        }
    });
}

/**
 * Send a message via API
 */
function sendMessageViaAPI(receiverId, content, callback) {
    apiPost('/api/messages/send', {
        receiver_id: receiverId,
        content: content
    }, callback);
}

/**
 * Mark notification as read
 */
function markNotificationRead(notifId) {
    apiPost('/api/notifications/' + notifId + '/read', {}, function(response) {
        if (response.success) {
            loadNotifications();
        }
    });
}

/**
 * Mark all notifications as read
 */
function markAllNotificationsRead() {
    apiPost('/api/notifications/read-all', {}, function(response) {
        if (response.success) {
            loadNotifications();
            showNotification('All notifications marked as read.', 'success');
        }
    });
}







/**
 * Preview a file upload
 * @param {Element} input - The file input element
 * @param {string} previewId - ID of the preview container
 */
function previewFile(input, previewId) {
    var preview = document.getElementById(previewId);
    if (!preview) return;
    
    var file = input.files[0];
    if (file) {
        if (file.size > 5 * 1024 * 1024) {
            showNotification('File too large. Maximum size is 5MB.', 'error');
            input.value = '';
            preview.innerHTML = '';
            return;
        }
        
        var reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = '<img src="' + e.target.result + '" alt="Preview" style="max-width:200px; border-radius:5px;">';
        };
        reader.readAsDataURL(file);
    }
}

/**
 * Update profile creation progress steps
 * @param {number} currentStep - Current step number
 * @param {number} totalSteps - Total number of steps
 */
function updateProfileSteps(currentStep, totalSteps) {
    totalSteps = totalSteps || 5;
    for (var i = 1; i <= totalSteps; i++) {
        var stepEl = document.getElementById('progressStep' + i);
        if (!stepEl) continue;
        
        var circle = stepEl.querySelector('.step-circle');
        var label = stepEl.querySelector('small');
        
        if (!circle || !label) continue;
        
        if (i < currentStep) {
            circle.style.background = '#00a65a';
            circle.style.color = 'white';
            label.style.color = '#00a65a';
        } else if (i === currentStep) {
            circle.style.background = '#3c8dbc';
            circle.style.color = 'white';
            label.style.color = '#3c8dbc';
        } else {
            circle.style.background = '#ddd';
            circle.style.color = '#999';
            label.style.color = '#999';
        }
        
        var lineEl = document.getElementById('progressLine' + i);
        if (lineEl) {
            lineEl.style.background = i < currentStep ? '#00a65a' : '#ddd';
        }
    }
}

/**
 * Show loading state in an element
 * @param {string} elementId - ID of the element
 */
function showLoading(elementId) {
    var el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div class="text-center" style="padding:40px;"><i class="fa fa-spinner fa-spin fa-3x" style="color:#3c8dbc;"></i><p style="margin-top:10px;">Loading...</p></div>';
    }
}

/**
 * Check if device is mobile
 * @returns {boolean}
 */
function isMobile() {
    return window.innerWidth <= 768;
}

/**
 * Check current page
 * @returns {string} Current page name
 */
function getCurrentPage() {
    var path = window.location.pathname;
    if (path === '/' || path === '/index') return 'home';
    return path.replace(/\//g, '_').replace(/^_|_$/g, '');
}