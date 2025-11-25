// Unified Drag Controller - Single Source of Truth for Drag Operations
// Eliminates double placeholder issue by architectural design

class UnifiedDragController {
    constructor() {
        // Core state
        this.placeholder = null;
        this.draggedElement = null;
        this.dragMode = null; // 'reorder' or 'hierarchy'
        this.dropTarget = null;
        this.isReordering = false;
        
        // Animation state
        this.originalRect = null;
        
        // Debug logging state
        this.lastLoggedMode = null;
        
        // Task list reference
        this.taskList = null;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    // Single entry point for all drag operations
    initialize() {
        this.taskList = document.querySelector('.task-list');
        if (!this.taskList) {
            console.warn('Task list not found. Drag controller disabled.');
            return;
        }
        
        this.setupEventListeners();
        console.log('Unified Drag Controller initialized');
    }
    
    // Setup all event listeners in one place
    setupEventListeners() {
        // Task list events
        this.taskList.addEventListener('dragover', this.handleDragOver.bind(this));
        this.taskList.addEventListener('drop', this.handleDrop.bind(this));
        
        // Individual task events
        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('dragstart', this.handleDragStart.bind(this));
            item.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }
    
    // Single drag start logic
    handleDragStart(e) {
        if (this.isReordering) return;
        
        this.draggedElement = e.target.closest('.task-item');
        if (!this.draggedElement) return;
        
        // Add visual feedback
        this.draggedElement.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.draggedElement.innerHTML);
        this.isReordering = true;
        
        // Store original position for animation
        this.originalRect = this.draggedElement.getBoundingClientRect();
        
        console.log('Drag started:', this.draggedElement.dataset.taskId);
    }
    
    // Single drag over logic - THE KEY FIX (WITH ENHANCED LOGGING)
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        if (!this.draggedElement) return;
        
        const targetElement = e.target.closest('.task-item');
        
        if (targetElement && targetElement !== this.draggedElement) {
            // SINGLE mode detection
            const newMode = this.detectDropMode(targetElement, e.clientX, e.clientY);
            this.dropTarget = targetElement;
            
            // Smart logging - only log when mode changes
            if (this.lastLoggedMode !== newMode) {
                console.log(`🎯 Mode changed: ${this.lastLoggedMode || 'none'} → ${newMode}`);
                this.lastLoggedMode = newMode;
            }
            
            // Update drag mode
            this.dragMode = newMode;
            
            // Add visual feedback for hierarchy mode
            this.updateVisualFeedback();
            
            // SINGLE placeholder positioning
            this.updatePlaceholderPosition(e);
        } else {
            this.dropTarget = null;
            this.dragMode = 'reorder';
            
            // Log mode change back to reorder
            if (this.lastLoggedMode !== 'reorder') {
                console.log(`🎯 Mode changed: ${this.lastLoggedMode || 'none'} → reorder`);
                this.lastLoggedMode = 'reorder';
            }
            
            // Remove visual feedback
            this.updateVisualFeedback();
            
            this.updatePlaceholderPosition(e);
        }
    }
    
    // Single drop logic (WITH ENHANCED LOGGING)
    handleDrop(e) {
        e.preventDefault();
        
        if (!this.draggedElement) return;
        
        console.log('🎯 Drop executed - Mode:', this.dragMode, 'Target:', this.dropTarget?.dataset.taskId);
        
        if (this.dragMode === 'hierarchy' && this.dropTarget) {
            console.log('🔗 Executing hierarchy creation...');
            this.createSubtaskRelationship();
        } else {
            console.log('🔄 Executing reordering...');
            this.performReorder();
        }
    }
    
    // Single drag end logic (WITH ENHANCED CLEANUP)
    handleDragEnd(e) {
        if (!this.draggedElement) return;
        
        console.log('🏁 Drag ended');
        
        // Centralized cleanup
        this.removePlaceholder();
        this.draggedElement.classList.remove('dragging');
        this.draggedElement = null;
        this.dropTarget = null;
        this.dragMode = null;
        this.isReordering = false;
        
        // Reset debug state
        this.lastLoggedMode = null;
        
        // Remove visual feedback
        this.updateVisualFeedback();
    }
    
    // Visual feedback for hierarchy mode
    updateVisualFeedback() {
        // Remove any existing hierarchy feedback
        document.querySelectorAll('.hierarchy-drop-target').forEach(el => {
            el.classList.remove('hierarchy-drop-target');
        });
        
        // Add hierarchy feedback if in hierarchy mode
        if (this.dragMode === 'hierarchy' && this.dropTarget) {
            this.dropTarget.classList.add('hierarchy-drop-target');
        }
    }
    
    // Sliding animation for dropped elements
    animateDrop(element) {
        if (!this.originalRect) return;
        
        // Get the new position after DOM insertion
        const newRect = element.getBoundingClientRect();
        
        // Calculate slide distance
        const slideDistance = this.originalRect.top - newRect.top;
        
        // Only animate if moved significantly (avoid micro-animations)
        if (Math.abs(slideDistance) > 5) {
            // Set initial transform position
            element.style.transform = `translateY(${slideDistance}px)`;
            element.style.transition = 'none';
            
            // Force DOM update
            element.offsetHeight; // Trigger reflow
            
            // Apply transition and animate to final position
            element.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            element.style.transform = 'translateY(0)';
            
            // Clean up after animation
            setTimeout(() => {
                element.style.transition = '';
                element.style.transform = '';
            }, 300);
        }
        
        // Reset original rect for next drag
        this.originalRect = null;
    }
    
    // Placeholder management - SINGLE SOURCE
    createPlaceholder() {
        // Remove ANY existing placeholders first (defensive programming)
        this.removePlaceholder();
        
        // Create EXACTLY ONE placeholder
        this.placeholder = document.createElement('li');
        this.placeholder.className = 'task-placeholder';
        this.placeholder.innerHTML = '<div class="placeholder-text">Drop task here</div>';
    }
    
    removePlaceholder() {
        // Remove ALL placeholders (defensive cleanup)
        document.querySelectorAll('.task-placeholder').forEach(p => p.remove());
        this.placeholder = null;
    }
    
    // Mode detection - SINGLE DECISION POINT (RIGHT HALF)
    detectDropMode(targetElement, x, y) {
        const rect = targetElement.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        
        // Simple: entire right half triggers hierarchy mode
        if (x > centerX && this.canBecomeSubtask(targetElement)) {
            return 'hierarchy';
        }
        return 'reorder';
    }
    
    // Check if target can become a parent (WITH ENHANCED LOGGING)
    canBecomeSubtask(targetElement) {
        const targetId = targetElement.dataset.taskId;
        const draggedId = this.draggedElement.dataset.taskId;
        
        // Prevent self-reference
        if (targetId === draggedId) {
            console.log('🚫 Cannot make task a subtask of itself');
            return false;
        }
        
        // Prevent circular references
        const isDescendant = this.isDescendant(targetId, draggedId);
        if (isDescendant) {
            console.log('🚫 Cannot make task a subtask of its own descendant');
            return false;
        }
        
        console.log('✅ Task can become subtask');
        return true;
    }
    
    // Check if potentialDescendant is actually a descendant of potentialAncestor
    isDescendant(potentialDescendant, potentialAncestor) {
        let current = potentialDescendant;
        while (current) {
            const parentId = document.querySelector(`[data-task-id="${current}"]`)?.dataset.parentId;
            if (parentId === potentialAncestor) {
                return true;
            }
            current = parentId;
        }
        return false;
    }
    
    // Update placeholder position based on current drag state
    updatePlaceholderPosition(e) {
        // Ensure placeholder exists
        if (!this.placeholder) {
            this.createPlaceholder();
        }
        
        const afterElement = this.getDragAfterElement(this.taskList, e.clientY);
        
        if (afterElement == null) {
            if (this.taskList.lastElementChild !== this.placeholder) {
                this.taskList.appendChild(this.placeholder);
            }
        } else {
            if (afterElement.previousElementSibling !== this.placeholder) {
                this.taskList.insertBefore(this.placeholder, afterElement);
            }
        }
    }
    
    // Get element after which to insert placeholder
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
    
    // Execute hierarchy creation (WITH COMPREHENSIVE LOGGING)
    createSubtaskRelationship() {
        console.log('🔗 Creating subtask relationship...');
        
        const draggedId = this.draggedElement.dataset.taskId;
        const targetId = this.dropTarget.dataset.taskId;
        
        console.log(`📝 Making task ${draggedId} a subtask of ${targetId}`);
        
        // Show loading state
        document.querySelectorAll('.task-item').forEach(el => el.style.opacity = '0.7');
        
        // Use the correct API endpoint for moving existing tasks
        fetch(`/task/${draggedId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                new_parent_id: targetId,
                operation: 'make_subtask'
            })
        })
        .then(response => {
            console.log('📡 Subtask API response:', response.status);
            console.log('📡 Response headers:', response.headers.get('content-type'));
            
            // Check if response is actually JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                // It's not JSON, likely an HTML error page
                return response.text().then(text => {
                    console.log('❌ API returned HTML instead of JSON:', text.substring(0, 200));
                    throw new Error('API returned HTML error page instead of JSON');
                });
            }
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 Subtask API data:', data);
            if (!data.success) {
                console.error('❌ Failed to create subtask:', data.error);
                this.showError('Failed to create subtask relationship');
                setTimeout(() => location.reload(), 2000);
            } else {
                console.log('✅ Subtask relationship created successfully');
                setTimeout(() => location.reload(), 500);
            }
        })
        .catch(error => {
            console.error('💥 Error creating subtask relationship:', error);
            this.showError('Error creating subtask relationship');
        })
        .finally(() => {
            // Restore opacity
            document.querySelectorAll('.task-item').forEach(el => el.style.opacity = '1');
        });
    }
    
    // Execute reordering
    performReorder() {
        const placeholder = document.querySelector('.task-placeholder');
        if (!placeholder || !placeholder.parentNode) return;
        
        console.log('Performing reorder');
        
        // Move dragged element to placeholder position
        placeholder.parentNode.insertBefore(this.draggedElement, placeholder);
        placeholder.remove();
        
        // Add sliding animation
        this.animateDrop(this.draggedElement);
        
        // Collect new order
        const taskElements = this.taskList.querySelectorAll('.task-item');
        const newOrder = Array.from(taskElements).map(el => el.dataset.taskId);
        const listId = this.taskList.dataset.listId;
        
        if (!newOrder.length || !listId) {
            console.error('Missing required data for reorder');
            this.isReordering = false;
            return;
        }
        
        // Show loading state
        taskElements.forEach(el => el.style.opacity = '0.7');
        
        // Save new order
        fetch('/task/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                task_order: newOrder,
                list_id: listId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Failed to reorder tasks:', data.error);
                this.showError('Failed to reorder tasks');
                setTimeout(() => location.reload(), 2000);
            } else {
                taskElements.forEach(el => el.style.opacity = '1');
                // Success - no message needed per previous implementation
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
    
    // Utility: Get CSRF token
    getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    // Utility: Show error message
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

// Initialize the unified controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if no other drag system is active
    if (typeof TaskReordering === 'undefined' && typeof HierarchicalTaskReordering === 'undefined') {
        new UnifiedDragController();
    } else {
        console.warn('Other drag systems detected. Unified controller disabled to prevent conflicts.');
    }
});
