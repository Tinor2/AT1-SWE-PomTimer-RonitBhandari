# Hierarchical Tasks Usage Guide

## Current Issues & Analysis

### Issue 1: Double Red Boxes During Drag-and-Drop

**Problem**: When dragging tasks, two red boxes appear instead of proper visual feedback.

**Root Cause Analysis**:
- The original `TaskReordering` class creates a placeholder element for reordering
- The new `HierarchicalTaskReordering` class adds subtask drop zones with `.drag-over-parent` class
- Both systems are active simultaneously, causing conflicting visual feedback
- The placeholder from the parent class and the subtask drop zone from the child class both show red borders

**Files Involved**:
- `pomodoro/static/js/task-reorder.js` (line 29: placeholder creation)
- `pomodoro/static/js/hierarchical-tasks.js` (line 322: showSubtaskDropZone)
- `pomodoro/static/css/hierarchy.css` (line 192: .drag-over-parent styling)

**Roadmap to Fix**:
1. **Phase 1**: Modify `HierarchicalTaskReordering` to properly override placeholder behavior
2. **Phase 2**: Consolidate visual feedback systems to prevent conflicts
3. **Phase 3**: Test drag-and-drop to ensure only one visual indicator appears

### Issue 2: Drag-and-Drop Subtask Creation Not Working

**Problem**: Users want to drag tasks onto existing tasks to create subtasks, but this functionality isn't working properly.

**Root Cause Analysis**:
- The `detectDropZone()` method in `hierarchical-tasks.js` uses complex coordinate detection
- Drop zone detection requires specific positioning (top-third + right of center)
- The visual feedback for subtask zones may not be clear enough
- The parent class `handleListDragOver()` might interfere with child class logic

**Files Involved**:
- `pomodoro/static/js/hierarchical-tasks.js` (lines 332-343: detectDropZone method)
- `pomodoro/static/js/hierarchical-tasks.js` (lines 17-42: handleListDragOver override)

**Roadmap to Fix**:
1. **Phase 1**: Simplify drop zone detection to more intuitive areas
2. **Phase 2**: Improve visual feedback for subtask creation zones
3. **Phase 3**: Ensure proper coordination between parent and child drag handlers
4. **Phase 4**: Add user testing to validate intuitive drag-and-drop behavior

### Issue 3: Inconsistent Subtask Formatting

**Problem**: Subtasks have strange formatting with weird iconography instead of clean indentation.

**Root Cause Analysis**:
- Current implementation adds complex hierarchy controls, collapse buttons, and level indicators
- The `.level-indicator` creates vertical lines instead of simple indentation
- Multiple UI elements (collapse btn, add subtask btn, level indicator) clutter the interface
- The styling tries to show hierarchy through visual elements rather than clean spacing

**Files Involved**:
- `pomodoro/templates/home/index.html` (lines 62-75: hierarchy controls)
- `pomodoro/static/css/hierarchy.css` (lines 10-16: level-indicator styling)
- `pomodoro/static/css/hierarchy.css` (lines 100-140: level-based styling)

**Roadmap to Fix**:
1. **Phase 1**: Remove complex hierarchy controls from template
2. **Phase 2**: Replace level-indicator divs with simple CSS padding/margin
3. **Phase 3**: Clean up add-subtask buttons and collapse buttons
4. **Phase 4**: Ensure consistent styling across all task levels

### Issue 4: Unnecessary Collapse Arrows

**Problem**: Collapse arrows appear on all tasks but only make sense for parent tasks with children.

**Root Cause Analysis**:
- Template shows collapse buttons for all level-0 tasks regardless of whether they have children
- The `updateCollapseButtons()` method should hide buttons for tasks without children
- Current logic shows buttons with `style="display: none;"` but doesn't dynamically update based on actual children

**Files Involved**:
- `pomodoro/templates/home/index.html` (lines 68-74: collapse button logic)
- `pomodoro/static/js/hierarchical-tasks.js` (lines 340-350: updateCollapseButtons method)

**Roadmap to Fix**:
1. **Phase 1**: Remove collapse buttons from template entirely
2. **Phase 2**: Simplify task hierarchy display to focus on indentation only
3. **Phase 3**: (Future) Re-add collapse functionality only when needed

---

## Overview
The hierarchical tasks feature allows you to organize tasks in a parent-child relationship, creating subtasks and nested structures.

## Features Implemented

### 1. Database Schema
- ✅ Added `parent_id`, `level`, and `path` fields to tasks table
- ✅ Created indexes for optimal performance
- ✅ Migration script applied to existing data

### 2. Backend API
- ✅ `POST /task/<parent_id>/subtask` - Create subtask
- ✅ `POST /task/<id>/move` - Move task to new parent or root level
- ✅ `GET /tasks/tree` - Get hierarchical task structure
- ✅ Circular reference prevention
- ✅ Recursive path and level updates

### 3. Frontend Interface
- ✅ Visual hierarchy with indentation and connection lines
- ✅ Drag-and-drop to create subtasks (drag to top-right of target)
- ✅ Add subtask buttons on each task
- ✅ Collapse/expand functionality for parent tasks
- ✅ Level-based visual styling

## How to Use

### Creating Subtasks

#### Method 1: Drag and Drop
1. Drag any task and drop it in the **top-right area** of another task
2. The task will become a subtask of the target
3. Visual feedback shows when you're in the "subtask drop zone"

#### Method 2: Add Subtask Button
1. Click the `+` button next to any task
2. Type the subtask content in the input field
3. Press Enter or click "Add"

#### Method 3: API (for developers)
```javascript
fetch('/task/5/subtask', {
    method: 'POST',
    body: formData,
    headers: { 'X-CSRFToken': csrfToken }
})
```

### Managing Hierarchy

#### Collapse/Expand
- Click the arrow button next to parent tasks to show/hide subtasks
- Collapsed state is preserved during the session

#### Visual Indicators
- **Level 0** (Root): Bold text, white background
- **Level 1**: Blue left border, light gray background  
- **Level 2**: Cyan left border, darker gray background
- **Level 3+**: Accent colored borders with progressive indentation

#### Drag and Drop Modes
- **Reorder**: Drag to middle/bottom of tasks to reorder at same level
- **Create Subtask**: Drag to top-right corner to create hierarchy

### Safety Features

#### Circular Reference Prevention
- Cannot make a task a subtask of its own descendant
- Automatic detection and error message

#### Data Integrity
- All descendants are updated when parent changes
- Paths and levels maintained automatically
- Foreign key constraints ensure consistency

## Testing the Implementation

### 1. Start the Application
```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Start the Flask app
python app.py
# or
flask run
```

### 2. Test Basic Operations
1. **Create a root task**: Use the main "Add Task" input
2. **Create a subtask**: Click the `+` button on the root task
3. **Test drag-and-drop**: Drag another task onto the root task
4. **Test collapse**: Click the arrow button on the parent task
5. **Test reorder**: Drag tasks to reorder within the same level

### 3. Verify Database Structure
```bash
# Check hierarchical fields
sqlite3 instance/pomodoro.sqlite "SELECT id, parent_id, level, path FROM tasks;"

# Test hierarchical query
sqlite3 instance/pomodoro.sqlite "
WITH RECURSIVE task_tree AS (
    SELECT id, content, parent_id, level, path FROM tasks WHERE parent_id IS NULL
    UNION ALL
    SELECT t.id, t.content, t.parent_id, t.level, t.path 
    FROM tasks t JOIN task_tree tt ON t.parent_id = tt.id
)
SELECT * FROM task_tree ORDER BY path;
"
```

## Technical Details

### Database Schema
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_done BOOLEAN DEFAULT 0,
    tags TEXT DEFAULT '',
    position INTEGER DEFAULT 0,
    parent_id INTEGER DEFAULT NULL,     -- New: References parent task
    level INTEGER DEFAULT 0,            -- New: Hierarchy depth
    path TEXT DEFAULT NULL,             -- New: Materialized path (e.g., "1/5/12")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### JavaScript Architecture
- `HierarchicalTaskReordering` extends `TaskReordering`
- Preserves all existing drag-and-drop functionality
- Adds hierarchy detection and creation
- Maintains compatibility with existing code

### Performance Optimizations
- **Materialized Path**: `path` field enables efficient tree queries
- **Indexes**: On `parent_id`, `level`, and `path` for fast lookups
- **Recursive CTE**: Efficient hierarchical queries in SQL
- **Lazy Loading**: Subtasks loaded only when needed

## Troubleshooting

### Common Issues

#### Migration Not Applied
```bash
# Re-run migration
sqlite3 instance/pomodoro.sqlite < migrations/001_add_hierarchy.sql
```

#### JavaScript Errors
- Check browser console for errors
- Ensure `TaskReordering` class loads before `HierarchicalTaskReordering`
- Verify all CSS and JS files are included in template

#### Drag-and-Drop Not Working
- Check that `draggable="true"` is set on task items
- Verify `hierarchical-tasks.js` is loaded after `task-reorder.js`
- Test in different browsers (Chrome, Firefox, Safari)

#### Subtasks Not Showing
- Verify database fields are populated correctly
- Check that `get_tasks_with_hierarchy()` is being called
- Ensure template uses the new hierarchical data structure

### Debug Mode
Enable Flask debug mode for detailed error messages:
```bash
export FLASK_ENV=development
flask run
```

## Future Enhancements

### Planned Features
- **Progress Tracking**: Parent task completion based on subtasks
- **Bulk Operations**: Move entire subtask trees
- **Keyboard Shortcuts**: Quick subtask creation
- **Mobile Touch Support**: Better mobile drag-and-drop
- **Task Templates**: Predefined hierarchical structures

### Performance Improvements
- **Virtual Scrolling**: For large task trees
- **Caching**: Cache frequently accessed hierarchies
- **WebSocket Updates**: Real-time collaboration

## Support

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Verify the database schema with the test script
3. Review the Flask logs for backend errors
4. Run the test suite: `python test_hierarchy.py`

The implementation is designed to be backward compatible and should not interfere with existing task functionality.
