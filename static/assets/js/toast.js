/* Sweetalert Toast Config */
const Toast = Swal.mixin({
    // Creates toast notifications instead of modal popups
    toast: true,
    // Shows in bottom-end corner
    position: "bottom-end",
    // White icon color
    iconColor: "white",
    // Custom CSS class for styling
    customClass: {
        popup: "colored-toast",
    },
    // No confirm button needed for notifications
    showConfirmButton: false,
    // Auto dismiss after 2.5 seconds
    timer: 2500,
    // Shows progress bar for timer
    timerProgressBar: true,
});

// Add CSS for toast styling
const style = document.createElement('style');
style.textContent = `
.colored-toast.swal2-icon-success {
    background-color: #28a745 !important;
    color: white !important;
}
.colored-toast.swal2-icon-error {
    background-color: #dc3545 !important;
    color: white !important;
}
.colored-toast.swal2-icon-warning {
    background-color: #ffc107 !important;
    color: black !important;
}
.colored-toast.swal2-icon-info {
    background-color: #17a2b8 !important;
    color: white !important;
}
`;
document.head.appendChild(style);
