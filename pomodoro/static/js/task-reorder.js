class TaskReordering {
    constructor() {
        this.draggedElement = null;
        this.placeholder = null;
        this.isReordering = false;
        this.init();
    }
    
    init() {
        this.createPlaceholder();
        this.setupTaskList();
    }
    
    setupTaskList() {
        const taskList = document.querySelector('.task-list');
        if (!taskList) return;
        
        // Set up the task list container
        taskList.addEventListener('dragover', this.handleListDragOver.bind(this));
        taskList.addEventListener('drop', this.handleListDrop.bind(this));
        
        // Set up individual task items
        document.querySelectorAll('.task-item').forEach(item => {
            this.setupDragEvents(item);
        });
    }
    
    createPlaceholder() {
        // Remove any previous leftover placeholder
        const old = document.querySelector('.task-placeholder');
        if (old) old.remove();

        this.placeholder = document.createElement('li');
        this.placeholder.className = 'task-placeholder';
        this.placeholder.innerHTML = '<div class="placeholder-text">Drop task here</div>';
    }
    
    setupDragEvents(item) {
        item.addEventListener('dragstart', this.handleDragStart.bind(this));
        item.addEventListener('dragend', this.handleDragEnd.bind(this));
    }
    
    handleDragStart(e) {
        if (this.isReordering) return;
        
        this.draggedElement = e.target.closest('.task-item');
        if (!this.draggedElement) return;
        
        // Store original position for slide animation
        this.originalRect = this.draggedElement.getBoundingClientRect();
        
        this.draggedElement.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.draggedElement.innerHTML);
        this.isReordering = true;
    }
    
    handleListDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        if (!this.draggedElement) return;
        
        const taskList = e.currentTarget;
        const afterElement = this.getDragAfterElement(taskList, e.clientY);
        
        if (afterElement == null) {
            if (taskList.lastElementChild !== this.placeholder) {
                taskList.appendChild(this.placeholder);
            }
        } else {
            if (afterElement.previousElementSibling !== this.placeholder) {
                taskList.insertBefore(this.placeholder, afterElement);
            }
        }
    }
    
    handleListDrop(e) {
        e.preventDefault();
        if (!this.draggedElement) return;
        
        const taskList = e.currentTarget;
        const placeholder = document.querySelector('.task-placeholder');
        
        if (placeholder && placeholder.parentNode === taskList) {
            taskList.insertBefore(this.draggedElement, placeholder);
            placeholder.remove();
        }
        
        // Add drop animation
        this.animateDrop(this.draggedElement);
        
        this.saveNewOrder();
    }
    
    animateDrop(element) {
        // Get the new position
        const newRect = element.getBoundingClientRect();
        
        // Calculate the distance to slide
        const deltaY = this.originalRect.top - newRect.top;
        
        // Only animate if there's actual movement
        if (Math.abs(deltaY) > 5) {
            // Start from original position
            element.style.transition = 'none';
            element.style.transform = `translateY(${deltaY}px)`;
            
            // Force reflow
            element.offsetHeight;
            
            // Animate to final position
            element.style.transition = 'transform 0.25s ease-out';
            element.style.transform = 'translateY(0)';
            
            // Clean up after animation
            setTimeout(() => {
                element.style.transition = '';
                element.style.transform = '';
            }, 300);
        } else {
            // For small movements, just use the scale animation
            element.style.transition = 'transform 0.2s ease-out';
            element.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 100);
            
            setTimeout(() => {
                element.style.transition = '';
            }, 300);
        }
    }
    
    handleDragEnd(e) {
        if (!this.draggedElement) return;
        
        this.draggedElement.classList.remove('dragging');
        
        // Remove ALL placeholders, not just the first
        document.querySelectorAll('.task-placeholder').forEach(p => p.remove());

        this.draggedElement = null;
        this.isReordering = false;
    }
    
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.task-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    saveNewOrder() {
        const taskElements = document.querySelectorAll('.task-item');
        const taskOrder = Array.from(taskElements).map(el => el.dataset.taskId);
        const listId = document.querySelector('.task-list')?.dataset.listId;
        
        if (!taskOrder.length || !listId) {
            this.isReordering = false;
            return;
        }
        
        // Show loading state
        taskElements.forEach(el => el.style.opacity = '0.7');
        
        fetch('/task/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                task_order: taskOrder,
                list_id: listId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                console.error('Failed to reorder tasks:', data.error);
                this.showError('Failed to reorder tasks');
                setTimeout(() => location.reload(), 2000);
            } else {
                taskElements.forEach(el => el.style.opacity = '1');
                // Success message removed - showSuccess method was deleted
            }
        })
        .catch(error => {
            console.error('Error reordering tasks:', error);
            this.showError('Error reordering tasks');
            setTimeout(() => location.reload(), 2000);
        })
        .finally(() => {
            this.isReordering = false;
        });
    }
    
    getCsrfToken() {
        // Try multiple methods to get CSRF token
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return decodeURIComponent(value);
            }
        }
        
        return '';
    }
    
    showError(message) {
        const flashDiv = document.createElement('div');
        flashDiv.className = 'flash flash-error';
        flashDiv.textContent = message;
        flashDiv.style.position = 'fixed';
        flashDiv.style.top = '20px';
        flashDiv.style.right = '20px';
        flashDiv.style.zIndex = '9999';
        
        document.body.appendChild(flashDiv);
        setTimeout(() => flashDiv.remove(), 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TaskReordering();
});
