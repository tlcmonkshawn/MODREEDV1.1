/** Reed Orb animation controller */
class ReedOrb {
    constructor() {
        this.orb = document.getElementById('reed-orb');
        this.currentState = 'idle'; // idle, speaking, listening
        this.init();
    }
    
    init() {
        if (!this.orb) return;
        this.setIdle();
    }
    
    setState(state) {
        if (this.currentState === state) return;
        
        // Remove all state classes
        this.orb.classList.remove('speaking', 'listening', 'idle');
        
        // Add new state class
        this.currentState = state;
        if (state !== 'idle') {
            this.orb.classList.add(state);
        }
    }
    
    setSpeaking() {
        this.setState('speaking');
    }
    
    setListening() {
        this.setState('listening');
    }
    
    setIdle() {
        this.setState('idle');
    }
}

// Initialize Reed Orb
const reedOrb = new ReedOrb();

