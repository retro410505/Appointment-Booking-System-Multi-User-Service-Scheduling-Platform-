/* ==============================================================================
   Appointment Booking System - Client Scripts
   ==============================================================================
   Handles interactive UI behaviors such as dismissible flash alerts,
   form accessibility enhancements, and responsive components.
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // --------------------------------------------------------------------------
    // 1. Flash Message Auto-Dismissal
    // --------------------------------------------------------------------------
    // Automatically fades out informational flash notifications after 5 seconds,
    // while leaving critical error messages visible until dismissed.
    const flashMessages = document.querySelectorAll('.alert-success, .alert-info');

    flashMessages.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                alert.remove();
            }, 400);
        }, 5000);
    });

    // --------------------------------------------------------------------------
    // 2. Foundation Initialization Confirmation
    // --------------------------------------------------------------------------
    console.log('[Appointment Booking System] Frontend scripts loaded successfully.');
});
