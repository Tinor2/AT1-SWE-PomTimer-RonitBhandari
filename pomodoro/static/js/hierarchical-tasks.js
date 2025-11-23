// Hierarchical Task Management - Extends TaskReordering
class HierarchicalTaskReordering extends TaskReordering {
    constructor() {
        super();
        this.dragMode = null; // 'reorder' or 'hierarchy'
        this.dropTarget = null;
        this.initHierarchyFeatures();
    }
    
    initHierarchyFeatures() {
        // No additional features needed for simple indentation
    }
    
    // Override handleListDragOver to detect hierarchy vs reorder
    handleListDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        if (!this.draggedElement) return;
        
        const taskList = e.currentTarget;
        const targetElement = e.target.closest('.task-item');
        
        if (targetElement && targetElement !== this.draggedElement) {
            // Detect if we're creating a subtask or reordering
            const dropZone = this.detectDropZone(targetElement, e.clientX, e.clientY);
            
            if (dropZone.type === 'subtask' && this.canBecomeSubtask(targetElement)) {
                // Hierarchy mode - use parent logic but remember the target
                this.dropTarget = targetElement;
                this.dragMode = 'hierarchy';
                super.handleListDragOver(e); // Use parent placeholder
            } else {
                // Reorder mode
                this.dropTarget = null;
                this.dragMode = 'reorder';
                super.handleListDragOver(e); // Use parent placeholder
            }
        } else {
            // Use existing reorder logic
            this.dropTarget = null;
            this.dragMode = 'reorder';
            super.handleListDragOver(e);
        }
    }
    
    // Override handleListDrop to handle both operations
    handleListDrop(e) {
        e.preventDefault();
        
        if (this.dragMode === 'hierarchy' && this.dropTarget) {
            this.createSubtaskRelationship();
        } else {
            // Use parent class reorder logic
            super.handleListDrop(e);
        }
    }
    
    detectDropZone(targetElement, x, y) {
        const rect = targetElement.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const topThird = rect.top + rect.height / 3;
        
        // If dropped in top third and slightly to the right, create subtask
        if (y < topThird && x > centerX + 20) {
            return { type: 'subtask', element: targetElement };
        }
        
        return { type: 'reorder', element: targetElement };
    }
    
    canBecomeSubtask(targetElement) {
        // Prevent circular references
        const targetId = targetElement.dataset.taskId;
        const draggedId = this.draggedElement.dataset.taskId;
        
        if (targetId === draggedId) return false;
        
        // Check if target is a descendant of dragged element
        return !this.isDescendant(targetId, draggedId);
    }
    
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
    
    createSubtaskRelationship() {
        const draggedId = this.draggedElement.dataset.taskId;
        const targetId = this.dropTarget.dataset.taskId;
        
        // Show loading state
        document.querySelectorAll('.task-item').forEach(el => el.style.opacity = '0.7');
        
        fetch(`/task/${targetId}/subtask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                task_id: draggedId
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
                console.error('Failed to create subtask relationship:', data.error);
                this.showError('Failed to create subtask relationship');
                setTimeout(() => location.reload(), 2000);
            } else {
                // Reload to show updated hierarchy
                setTimeout(() => location.reload(), 500);
            }
        })
        .catch(error => {
            console.error('Error creating subtask relationship:', error);
            this.showError('Error creating subtask relationship');
        })
        .finally(() => {
            // Restore opacity
            document.querySelectorAll('.task-item').forEach(el => el.style.opacity = '1');
        });
    }
    
    // Override handleDragEnd to clean up hierarchy-specific states
    handleDragEnd(e) {
        // Reset hierarchy-specific states
        this.dropTarget = null;
        this.dragMode = null;
        
        // Call parent method
        super.handleDragEnd(e);
    }
}

// Initialize the enhanced class when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if TaskReordering is available
    if (typeof TaskReordering !== 'undefined') {
        new HierarchicalTaskReordering();
    } else {
        console.warn('TaskReordering class not found. Hierarchical features disabled.');
    }
});
