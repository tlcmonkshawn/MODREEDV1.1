/** Main application JavaScript */
class LiveAPIApp {
    constructor() {
        this.videoStream = null;
        this.audioContext = null;
        this.isRecording = false;
        this.recordingStartTime = null;
        this.capturedItems = [];
        this.isPortrait = window.innerHeight > window.innerWidth;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupResponsive();
        this.startCamera();
    }
    
    setupEventListeners() {
        // Control buttons
        document.getElementById('flip-btn')?.addEventListener('click', () => this.flipCamera());
        document.getElementById('snap-btn')?.addEventListener('click', () => this.captureSnapshot());
        document.getElementById('mute-btn')?.addEventListener('click', () => this.toggleMute());
        
        // Drawer controls
        document.getElementById('close-drawer')?.addEventListener('click', () => this.closeDrawer());
        document.getElementById('close-alert')?.addEventListener('click', () => this.closeAlert());
        
        // Transcript toggle
        document.getElementById('toggle-transcript')?.addEventListener('click', () => this.toggleTranscript());
    }
    
    setupResponsive() {
        window.addEventListener('resize', () => {
            this.isPortrait = window.innerHeight > window.innerWidth;
        });
    }
    
    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 768, height: 768 },
                audio: true
            });
            
            this.videoStream = stream;
            this.displayVideo(stream);
            this.startRecordingTimer();
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Failed to access camera. Please check permissions.');
        }
    }
    
    displayVideo(stream) {
        const canvas = document.getElementById('camera-canvas');
        const ctx = canvas.getContext('2d');
        const video = document.createElement('video');
        
        video.srcObject = stream;
        video.play();
        
        video.addEventListener('loadedmetadata', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        });
        
        const drawFrame = () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            }
            requestAnimationFrame(drawFrame);
        };
        
        drawFrame();
        
        // Also display in bootie viewer
        const bootieCanvas = document.getElementById('bootie-video-canvas');
        if (bootieCanvas) {
            const bootieCtx = bootieCanvas.getContext('2d');
            const bootieDrawFrame = () => {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    bootieCtx.drawImage(video, 0, 0, bootieCanvas.width, bootieCanvas.height);
                }
                requestAnimationFrame(bootieDrawFrame);
            };
            bootieDrawFrame();
        }
    }
    
    flipCamera() {
        // Implementation for camera flip
        console.log('Flip camera');
        // This would require stopping current stream and starting with different facingMode
    }
    
    async captureSnapshot() {
        const canvas = document.getElementById('camera-canvas');
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Send snapshot to backend
        try {
            const response = await fetch('/api/snapshot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            if (result.success) {
                this.addCapturedItem(result.item);
                this.showItemNotification(result.item);
            }
        } catch (error) {
            console.error('Error capturing snapshot:', error);
        }
    }
    
    addCapturedItem(item) {
        this.capturedItems.unshift(item);
        this.updateItemDrawer();
        this.updateLastItem(item);
    }
    
    updateItemDrawer() {
        const itemList = document.getElementById('item-list');
        if (!itemList) return;
        
        itemList.innerHTML = this.capturedItems.slice(0, 10).map(item => `
            <div class="item-card" data-id="${item.id}">
                <img src="/static/images/${item.filename}" alt="${item.name || 'Snapshot'}">
                <div class="item-name">${item.name || 'Unnamed'}</div>
                <div class="item-status">${item.state}</div>
            </div>
        `).join('');
        
        // Open drawer if in landscape mode
        if (!this.isPortrait) {
            const drawer = document.getElementById('item-drawer');
            if (drawer) {
                drawer.classList.add('open');
            }
        }
    }
    
    updateLastItem(item) {
        document.getElementById('last-item-name').textContent = item.name || '-';
        document.getElementById('last-item-status').textContent = item.state || 'CAPTURED';
        
        // Also update Bootie Viewer if available
        if (window.bootieViewer) {
            window.bootieViewer.updateLastItem(item);
        }
    }
    
    showItemNotification(item) {
        if (this.isPortrait) {
            // Show alert in portrait mode
            const alert = document.getElementById('portrait-alert');
            if (alert) {
                alert.classList.add('show');
            }
        }
    }
    
    closeDrawer() {
        const drawer = document.getElementById('item-drawer');
        if (drawer) {
            drawer.classList.remove('open');
        }
    }
    
    closeAlert() {
        const alert = document.getElementById('portrait-alert');
        if (alert) {
            alert.classList.remove('show');
        }
    }
    
    toggleMute() {
        // Implementation for mute toggle
        console.log('Toggle mute');
    }
    
    startRecordingTimer() {
        this.isRecording = true;
        this.recordingStartTime = Date.now();
        
        const updateTimer = () => {
            if (!this.isRecording) return;
            
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            const timerEl = document.getElementById('rec-timer');
            if (timerEl) {
                timerEl.textContent = `REC ${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            
            setTimeout(updateTimer, 1000);
        };
        
        updateTimer();
    }
    
    toggleTranscript() {
        const content = document.getElementById('transcript-content');
        const toggle = document.getElementById('toggle-transcript');
        
        if (content && toggle) {
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '−';
            } else {
                content.style.display = 'none';
                toggle.textContent = '+';
            }
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LiveAPIApp();
});

