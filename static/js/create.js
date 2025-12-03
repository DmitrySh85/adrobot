(function() {
    const wrapper = document.getElementById('toast-wrapper');
    if (!wrapper) return;

    const toasts = wrapper.querySelectorAll('.toast');

    toasts.forEach((toast, idx) => {
        setTimeout(() => toast.classList.add('show'), 100 * idx);

        setTimeout(() => {
            toast.classList.remove('show');

            setTimeout(() => toast.remove(), 300);

        }, 5000 + idx * 200);
    });
})();
