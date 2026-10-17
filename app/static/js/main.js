document.addEventListener('DOMContentLoaded', function() {
    console.log('Citizen Grievance System loaded.');

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
});
