# Task Reordering Implementation Plan

## Overview
This document outlines the approach for implementing drag-and-drop task reordering functionality.

## Current State Analysis
- Tasks are currently ordered by `created_at` timestamp
- No position/order field exists in the tasks table
- Frontend uses static list rendering without drag functionality
- No API endpoints exist for reordering tasks

## Implementation Plan

### Phase 1: Database Schema Update
- [ ] Add `position` column to tasks table
- [ ] Update existing tasks to have sequential positions
- [ ] Modify database queries to order by position instead of created_at
- [ ] Update task creation to assign proper position

### Phase 2: Backend API Endpoints
- [ ] Create new endpoint for reordering tasks (`/task/reorder`)
- [ ] Update existing task creation to handle positioning
- [ ] Update task deletion to reposition remaining tasks
- [ ] Add validation for position updates

### Phase 3: Frontend Drag-and-Drop
- [ ] Add drag-and-drop JavaScript library or custom implementation
- [ ] Update task list HTML to support dragging
- [ ] Implement visual feedback during dragging
- [ ] Add API calls to save new positions

### Phase 4: User Experience
- [ ] Add visual indicators for draggable items
- [ ] Implement smooth animations during reordering
- [ ] Handle edge cases (empty lists, single tasks)
- [ ] Add loading states during position updates

## Detailed Implementation Steps

### Database Schema Changes

**Add position column:**
```sql
ALTER TABLE tasks ADD COLUMN position INTEGER;

-- Update existing tasks to have sequential positions within each list
UPDATE tasks SET position = (
    SELECT row_number - 1
    FROM (
        SELECT id, row_number() OVER (ORDER BY created_at) as row_number
        FROM tasks 
        WHERE user_id = ? AND list_id = ?
    ) as numbered
    WHERE numbered.id = tasks.id
);
```

**Update queries to order by position:**
```sql
-- Before
SELECT * FROM tasks WHERE list_id = ? AND user_id = ? ORDER BY created_at

-- After  
SELECT * FROM tasks WHERE list_id = ? AND user_id = ? ORDER BY position
```

### Backend Changes

**New reorder endpoint:**
```python
@bp.route('/task/reorder', methods=['POST'])
@login_required
def reorder_tasks():
    """Update task positions based on drag-and-drop."""
    task_order = request.json.get('task_order', [])  # [task_id, task_id, ...]
    list_id = request.json.get('list_id')
    
    # Validate ownership
    if not verify_list_ownership(list_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update positions
    for index, task_id in enumerate(task_order):
        db.execute(
            'UPDATE tasks SET position = ? WHERE id = ? AND user_id = ?',
            (index, task_id, current_user.id)
        )
    
    db.commit()
    return jsonify({'success': True})
```

**Update task creation:**
```python
# Get highest position in the list
max_position = db.execute(
    'SELECT COALESCE(MAX(position), -1) FROM tasks WHERE list_id = ? AND user_id = ?',
    (list_id, current_user.id)
).fetchone()[0]

# Insert new task at the end
db.execute(
    'INSERT INTO tasks (list_id, user_id, content, position) VALUES (?, ?, ?, ?)',
    (list_id, current_user.id, content, max_position + 1)
)
```

### Frontend Implementation

**HTML Structure Updates:**
```html
<div class="task-list" data-list-id="{{ active_list.id }}">
    {% for task in tasks %}
    <div class="task-item" data-task-id="{{ task.id }}" draggable="true">
        <div class="drag-handle">⋮⋮</div>
        <!-- existing task content -->
    </div>
    {% endfor %}
</div>
```

**JavaScript Drag-and-Drop:**
```javascript
class TaskReordering {
    constructor() {
        this.draggedElement = null;
        this.init();
    }
    
    init() {
        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('dragstart', this.handleDragStart.bind(this));
            item.addEventListener('dragover', this.handleDragOver.bind(this));
            item.addEventListener('drop', this.handleDrop.bind(this));
            item.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }
    
    handleDragStart(e) {
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const afterElement = this.getDragAfterElement(e.currentTarget.parentNode, e.clientY);
        if (afterElement == null) {
            e.currentTarget.parentNode.appendChild(this.draggedElement);
        } else {
            e.currentTarget.parentNode.insertBefore(this.draggedElement, afterElement);
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.saveNewOrder();
    }
    
    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        this.draggedElement = null;
    }
    
    saveNewOrder() {
        const taskElements = document.querySelectorAll('.task-item');
        const taskOrder = Array.from(taskElements).map(el => el.dataset.taskId);
        const listId = document.querySelector('.task-list').dataset.listId;
        
        fetch('/task/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                task_order: taskOrder,
                list_id: listId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                // Handle error - maybe refresh the page
                location.reload();
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TaskReordering();
});
```

### CSS Styling

**Drag-and-drop styles:**
```css
.task-item {
    cursor: grab;
    transition: transform 0.2s, box-shadow 0.2s;
}

.task-item.dragging {
    opacity: 0.5;
    transform: rotate(2deg);
    cursor: grabbing;
}

.task-item:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.drag-handle {
    cursor: grab;
    color: #ccc;
    padding: 0 8px;
    user-select: none;
    font-size: 12px;
    display: flex;
    align-items: center;
}

.drag-handle:hover {
    color: #999;
}

.task-item.drag-over {
    border-top: 3px solid #ff5252;
}
```

## Files to Modify

### Backend
- `pomodoro/routes/home.py` - Add reorder endpoint, update task creation
- `pomodoro/db.py` - Add migration for position column
- `schema.sql` - Update schema for new installations

### Frontend  
- `pomodoro/templates/home/index.html` - Add drag handles and data attributes
- `pomodoro/static/js/task-reorder.js` - New JavaScript file for drag functionality
- `pomodoro/static/css/style.css` - Add drag-and-drop styles

## Implementation Order
1. Add position column to database
2. Update existing tasks with positions
3. Modify backend queries to use position ordering
4. Add reorder API endpoint
5. Update task creation logic
6. Implement frontend drag-and-drop
7. Add visual styling and animations
8. Test thoroughly

## Edge Cases to Handle
- Empty task lists
- Single task (no reordering needed)
- Concurrent users reordering same list
- Network errors during position updates
- Mobile touch events for dragging

## Success Criteria
- ✅ Tasks can be dragged to reorder
- ✅ New order is saved to database
- ✅ Visual feedback during dragging
- ✅ Works on both desktop and mobile
- ✅ Graceful error handling
- ✅ Existing functionality preserved
