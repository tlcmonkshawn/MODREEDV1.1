/** Image review and post-processing functionality */
class ImageReview {
    constructor() {
        this.currentItem = null;
        this.init();
    }
    
    init() {
        this.setupItemCardListeners();
    }
    
    setupItemCardListeners() {
        // Use event delegation for dynamically added items
        document.addEventListener('click', (e) => {
            const itemCard = e.target.closest('.item-card');
            if (itemCard) {
                const itemId = itemCard.dataset.id;
                this.openReviewModal(itemId);
            }
        });
    }
    
    async openReviewModal(itemId) {
        try {
            const response = await fetch(`/api/items/${itemId}`);
            const result = await response.json();
            
            if (result.success) {
                this.currentItem = result.item;
                this.showReviewModal();
            }
        } catch (error) {
            console.error('Error fetching item:', error);
        }
    }
    
    showReviewModal() {
        // Create or show review modal
        let modal = document.getElementById('review-modal');
        if (!modal) {
            modal = this.createReviewModal();
            document.body.appendChild(modal);
        }
        
        // Populate modal with item data
        const img = modal.querySelector('.review-image img');
        const nameInput = modal.querySelector('#item-name-input');
        const categoryInput = modal.querySelector('#item-category-input');
        const useBtn = modal.querySelector('#use-btn');
        const discardBtn = modal.querySelector('#discard-btn');
        
        if (img) img.src = `/static/images/${this.currentItem.filename}`;
        if (nameInput) nameInput.value = this.currentItem.name || '';
        if (categoryInput) categoryInput.value = this.currentItem.category || '';
        
        // Update button handlers
        useBtn.onclick = () => this.markAsUsed();
        discardBtn.onclick = () => this.markAsDiscarded();
        
        modal.classList.add('show');
    }
    
    createReviewModal() {
        const modal = document.createElement('div');
        modal.id = 'review-modal';
        modal.className = 'review-modal';
        modal.innerHTML = `
            <div class="review-modal-content">
                <div class="review-header">
                    <h3>Review Image</h3>
                    <button class="close-review-btn">&times;</button>
                </div>
                <div class="review-body">
                    <div class="review-image">
                        <img src="" alt="Review">
                    </div>
                    <div class="review-form">
                        <div class="form-group">
                            <label for="item-name-input">Name</label>
                            <input type="text" id="item-name-input" placeholder="Enter name">
                        </div>
                        <div class="form-group">
                            <label for="item-category-input">Category</label>
                            <input type="text" id="item-category-input" placeholder="Enter category">
                        </div>
                    </div>
                </div>
                <div class="review-footer">
                    <button id="use-btn" class="btn btn-primary">USE</button>
                    <button id="discard-btn" class="btn btn-secondary">DISCARD</button>
                    <button id="save-btn" class="btn btn-success">SAVE</button>
                </div>
            </div>
        `;
        
        // Close button handler
        modal.querySelector('.close-review-btn').onclick = () => {
            modal.classList.remove('show');
        };
        
        // Save button handler
        modal.querySelector('#save-btn').onclick = () => this.saveChanges();
        
        return modal;
    }
    
    async saveChanges() {
        if (!this.currentItem) return;
        
        const nameInput = document.getElementById('item-name-input');
        const categoryInput = document.getElementById('item-category-input');
        
        try {
            const response = await fetch(`/api/items/${this.currentItem.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: nameInput.value,
                    category: categoryInput.value
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.currentItem = result.item;
                // Update UI
                if (window.app) {
                    window.app.updateItemDrawer();
                }
                this.closeModal();
            }
        } catch (error) {
            console.error('Error saving changes:', error);
        }
    }
    
    async markAsUsed() {
        if (!this.currentItem) return;
        
        try {
            const response = await fetch(`/api/items/${this.currentItem.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state: 'USED' })
            });
            
            const result = await response.json();
            if (result.success) {
                this.currentItem = result.item;
                if (window.app) {
                    window.app.updateItemDrawer();
                }
                this.closeModal();
            }
        } catch (error) {
            console.error('Error marking as used:', error);
        }
    }
    
    async markAsDiscarded() {
        if (!this.currentItem) return;
        
        try {
            const response = await fetch(`/api/items/${this.currentItem.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state: 'DISCARDED' })
            });
            
            const result = await response.json();
            if (result.success) {
                this.currentItem = result.item;
                if (window.app) {
                    window.app.updateItemDrawer();
                }
                this.closeModal();
            }
        } catch (error) {
            console.error('Error marking as discarded:', error);
        }
    }
    
    closeModal() {
        const modal = document.getElementById('review-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }
}

// Initialize Image Review
const imageReview = new ImageReview();

