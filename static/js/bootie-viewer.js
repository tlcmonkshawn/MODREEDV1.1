/** Bootie Viewer functionality */
class BootieViewer {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupCameraSelect();
    }
    
    setupCameraSelect() {
        const dots = document.querySelectorAll('.camera-dot');
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                dots.forEach(d => d.classList.remove('active'));
                dot.classList.add('active');
                // Handle camera selection
                console.log(`Selected camera ${index}`);
            });
        });
    }
    
    updateLastItem(item) {
        const nameEl = document.getElementById('last-item-name');
        const statusEl = document.getElementById('last-item-status');
        
        if (nameEl) nameEl.textContent = item.name || '-';
        if (statusEl) statusEl.textContent = item.state || 'CAPTURED';
    }
}

// Initialize Bootie Viewer
const bootieViewer = new BootieViewer();

