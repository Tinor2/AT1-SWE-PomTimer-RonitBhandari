# Pomodoro Timer Implementation Roadmap

## Overview
This roadmap outlines the step-by-step process to implement a fully functional Pomodoro timer that's integrated with your to-do list system.

---

## Phase 1: Timer State Management & Database Setup

### 1.1 Extend Database Schema
**Goal**: Store timer state persistently across sessions

**Tasks**:
- [ ] Add new columns to `lists` table:
  - `timer_state` TEXT - Values: 'idle', 'session', 'short_break', 'long_break', 'paused'
  - `timer_remaining` INTEGER - Seconds remaining in current period
  - `sessions_completed` INTEGER - Number of Pomodoros completed (for long break logic)
  - `timer_started_at` TIMESTAMP - When the current timer started (for accurate time tracking)

**SQL Migration**:
```sql
ALTER TABLE lists ADD COLUMN timer_state TEXT DEFAULT 'idle';
ALTER TABLE lists ADD COLUMN timer_remaining INTEGER DEFAULT 0;
ALTER TABLE lists ADD COLUMN sessions_completed INTEGER DEFAULT 0;
ALTER TABLE lists ADD COLUMN timer_started_at TIMESTAMP;
```

**Files to Modify**:
- `schema.sql` - Add columns to CREATE TABLE statement
- Create migration script or re-run `flask init-db` (will lose data)

---

## Phase 2: Backend API Endpoints

### 2.1 Create Timer Control Routes
**Goal**: Handle timer operations (start, pause, reset, skip)

**New Routes in `pomodoro/routes/home.py`**:

- [ ] `POST /timer/start` - Start or resume timer
  - Get active list
  - Calculate remaining time based on current state
  - Update `timer_state` to 'session', 'short_break', or 'long_break'
  - Set `timer_started_at` to current timestamp
  - Return timer data as JSON

- [ ] `POST /timer/pause` - Pause the timer
  - Calculate elapsed time since `timer_started_at`
  - Update `timer_remaining` with calculated remaining time
  - Set `timer_state` to 'paused'
  - Return updated timer data

- [ ] `POST /timer/reset` - Reset timer to idle state
  - Set `timer_state` to 'idle'
  - Set `timer_remaining` to 0
  - Clear `timer_started_at`
  - Return success response

- [ ] `POST /timer/skip` - Skip to next phase
  - Determine next phase based on current state and sessions completed
  - If session completed, increment `sessions_completed`
  - Every 4 sessions, trigger long break instead of short break
  - Set appropriate timer duration
  - Return timer data

- [ ] `GET /timer/status` - Get current timer status
  - Calculate current remaining time if timer is running
  - Return complete timer state as JSON

**Response Format** (JSON):
```json
{
  "state": "session",
  "remaining": 1500,
  "duration": 1500,
  "sessions_completed": 2,
  "is_running": true
}
```

---

## Phase 3: Frontend Timer Display

### 3.1 Update Home Page HTML
**Goal**: Replace placeholder with functional timer interface

**File**: `templates/home/index.html`

**Components to Add**:
- [ ] Large digital timer display (MM:SS format)
- [ ] Current phase indicator ("Focus Session", "Short Break", "Long Break")
- [ ] Progress bar (visual representation of time elapsed)
- [ ] Control buttons:
  - Start/Pause button (toggles based on state)
  - Reset button
  - Skip button
- [ ] Sessions completed counter (e.g., "2/4 sessions until long break")

**HTML Structure**:
```html
<div class="timer-container">
  <div class="timer-phase">Focus Session</div>
  <div class="timer-display">25:00</div>
  <div class="timer-progress">
    <div class="progress-bar" style="width: 0%"></div>
  </div>
  <div class="timer-controls">
    <button id="startPauseBtn" class="btn btn-primary">Start</button>
    <button id="resetBtn" class="btn btn-secondary">Reset</button>
    <button id="skipBtn" class="btn btn-secondary">Skip</button>
  </div>
  <div class="timer-sessions">0/4 sessions</div>
</div>
```

---

## Phase 4: Frontend Timer Logic (JavaScript)

### 4.1 Create Timer JavaScript Module
**Goal**: Handle client-side timer countdown and UI updates

**File**: `static/js/home.js`

**Core Functions to Implement**:

- [ ] **`initTimer()`** - Initialize timer on page load
  - Fetch current timer status from `/timer/status`
  - Update UI with current state
  - If timer is running, start countdown

- [ ] **`startTimer()`** - Start the timer
  - Send POST request to `/timer/start`
  - Begin client-side countdown
  - Update button to show "Pause"

- [ ] **`pauseTimer()`** - Pause the timer
  - Send POST request to `/timer/pause`
  - Stop client-side countdown
  - Update button to show "Resume"

- [ ] **`resetTimer()`** - Reset to idle state
  - Send POST request to `/timer/reset`
  - Stop countdown
  - Reset display to default

- [ ] **`skipPhase()`** - Skip to next phase
  - Send POST request to `/timer/skip`
  - Update UI with new phase
  - Auto-start new phase (optional)

- [ ] **`updateDisplay(seconds)`** - Update timer display
  - Convert seconds to MM:SS format
  - Update DOM element with formatted time

- [ ] **`updateProgressBar(elapsed, total)`** - Update visual progress
  - Calculate percentage complete
  - Update progress bar width

- [ ] **`handleTimerComplete()`** - Handle timer reaching 0
  - Show notification (browser notification API)
  - Play sound alert (optional)
  - Automatically transition to next phase
  - Update sessions completed counter

- [ ] **`countdown()`** - Main countdown loop
  - Run every second using `setInterval`
  - Decrement remaining time
  - Update display and progress bar
  - Check if timer reached 0

**Key Variables**:
```javascript
let timerInterval = null;
let timerState = 'idle';
let remainingSeconds = 0;
let totalSeconds = 0;
let sessionsCompleted = 0;
```

---

## Phase 5: Timer Synchronization

### 5.1 Implement Server-Side Time Tracking
**Goal**: Ensure accurate timing even if user closes/refreshes page

**Strategy**:
- Store `timer_started_at` timestamp in database
- On status request, calculate elapsed time server-side:
  ```python
  elapsed = now - timer_started_at
  remaining = total_duration - elapsed
  ```
- This prevents drift from client-side JavaScript timers

**Files to Modify**:
- `pomodoro/routes/home.py` - Add time calculation logic

---

## Phase 6: User Experience Enhancements

### 6.1 Visual Feedback
- [ ] Add color coding for different phases:
  - Red/Orange for focus sessions
  - Green for short breaks
  - Blue for long breaks
- [ ] Animate timer display when running
- [ ] Pulse effect when timer completes
- [ ] Add favicon that updates with timer state

### 6.2 Audio Notifications
- [ ] Add sound file to `static/sounds/`
- [ ] Play completion sound when timer reaches 0
- [ ] Add option to mute/unmute

### 6.3 Browser Notifications
- [ ] Request notification permission on page load
- [ ] Send browser notification when timer completes
- [ ] Include phase information in notification

**JavaScript**:
```javascript
if (Notification.permission === "granted") {
  new Notification("Pomodoro Complete!", {
    body: "Time for a break!",
    icon: "/static/images/tomato-icon.png"
  });
}
```

### 6.4 Document Title Updates
- [ ] Update browser tab title with remaining time
- [ ] Example: "(23:45) Pomodoro Timer"
- [ ] Helps users track time without switching tabs

---

## Phase 7: Settings & Customization

### 7.1 Add Timer Settings Page (Future Enhancement)
**Goal**: Allow users to customize timer durations per list

**Features**:
- [ ] Edit session duration (default: 25 min)
- [ ] Edit short break duration (default: 5 min)
- [ ] Edit long break duration (default: 15 min)
- [ ] Edit number of sessions before long break (default: 4)
- [ ] Enable/disable auto-start next phase
- [ ] Enable/disable sound notifications

**Route**: `/lists/<int:id>/settings`

---

## Phase 8: Testing & Refinement

### 8.1 Test Cases
- [ ] Timer starts correctly from idle state
- [ ] Timer pauses and resumes correctly
- [ ] Timer resets to initial state
- [ ] Timer skips to next phase correctly
- [ ] Sessions counter increments after completed focus session
- [ ] Long break triggers after 4 completed sessions
- [ ] Timer state persists across page refreshes
- [ ] Timer continues accurately if user closes and reopens tab
- [ ] Switching active lists loads correct timer state
- [ ] Multiple browser tabs don't interfere with each other

### 8.2 Edge Cases to Handle
- [ ] User switches lists while timer is running (pause timer?)
- [ ] User deletes active list while timer is running (reset timer)
- [ ] Timer reaches 0 while tab is not in focus
- [ ] Network error during API call (retry logic)
- [ ] Time drift between client and server

---

## Phase 9: CSS Styling

### 9.1 Timer-Specific Styles
**File**: `static/css/style.css`

**Styles to Add**:
- [ ] `.timer-container` - Main timer wrapper
- [ ] `.timer-display` - Large digital timer text
- [ ] `.timer-phase` - Phase indicator styling
- [ ] `.timer-progress` - Progress bar container
- [ ] `.progress-bar` - Animated progress bar fill
- [ ] `.timer-controls` - Button layout
- [ ] `.timer-sessions` - Session counter styling
- [ ] Color variations for different states
- [ ] Animations for state transitions

---

## Implementation Order (Recommended)

### Week 1: Foundation
1. ✅ Phase 1.1 - Update database schema
2. ✅ Phase 2.1 - Create backend API endpoints
3. ✅ Phase 5.1 - Implement server-side time tracking

### Week 2: Core Functionality
4. ✅ Phase 3.1 - Update HTML with timer UI
5. ✅ Phase 4.1 - Implement JavaScript timer logic
6. ✅ Phase 9.1 - Add CSS styling

### Week 3: Polish
7. ✅ Phase 6.1 - Visual feedback
8. ✅ Phase 6.2 - Audio notifications
9. ✅ Phase 6.3 - Browser notifications
10. ✅ Phase 8 - Testing & bug fixes

### Future Enhancements
11. Phase 6.4 - Document title updates
12. Phase 7 - Settings customization
13. Statistics tracking (time spent in focus, breaks taken, etc.)

---

## Technical Notes

### Time Calculation Strategy
Instead of relying solely on JavaScript `setInterval` (which can drift), use a hybrid approach:

1. **Server stores**: `timer_started_at` timestamp
2. **Client displays**: Real-time countdown
3. **On refresh**: Recalculate remaining time from server timestamp
4. **Every 10 seconds**: Sync with server to prevent drift

### State Machine
```
idle -> session -> short_break -> session -> short_break -> session -> short_break -> session -> long_break -> idle
         ^                                                                                          |
         |                                                                                          |
         +-------------------------------------------(cycle repeats)-----------------------------------+
```

### Sessions Counter Logic
```python
if timer_state == 'session' and timer_completed:
    sessions_completed += 1
    if sessions_completed % 4 == 0:
        next_state = 'long_break'
    else:
        next_state = 'short_break'
```

---

## Files to Create/Modify Summary

### New Files:
- `static/sounds/timer-complete.mp3` (optional)

### Modified Files:
1. `schema.sql` - Add timer columns
2. `pomodoro/routes/home.py` - Add timer endpoints
3. `templates/home/index.html` - Replace placeholder with timer UI
4. `static/js/home.js` - Add timer JavaScript logic
5. `static/css/style.css` - Add timer styling

---

## Success Criteria

✅ User can start a 25-minute focus session
✅ User can pause and resume timer
✅ User can reset timer to idle state
✅ User can skip to next phase
✅ Timer automatically transitions between phases
✅ Long break occurs after 4 completed focus sessions
✅ Timer state persists across page refreshes
✅ Timer continues accurately even after tab close/reopen
✅ Browser notifications appear when timer completes
✅ Timer is linked to active list (switching lists loads that list's timer state)

---

## Notes & Considerations

- **Browser Tab Visibility**: Use Page Visibility API to detect when user switches tabs and adjust timing accordingly
- **Mobile Support**: Ensure timer works on mobile devices (iOS Safari, Android Chrome)
- **Accessibility**: Add ARIA labels for screen readers
- **Performance**: Use `requestAnimationFrame` for smooth animations instead of CSS transitions
- **Data Loss Prevention**: Warn user if they try to close tab with active timer

---

*This roadmap provides a complete implementation guide. Start with Phase 1 and work sequentially for best results.*

# Pomodoro Timer Implementation — Step-by-Step Instructions (For AI Execution)

This document breaks the roadmap into extremely clear, granular, spoon-fed instructions that another AI model can execute without needing interpretation. Follow each step in order.

---

# ⚠️ BEFORE STARTING

* Ensure the project runs without errors.
* Ensure you have access to: `schema.sql`, `/routes/`, `/templates/`, `/static/js/`, `/static/css/`, `/db.py`, and the Flask app factory.
* Every code change MUST be implemented exactly as instructed.

---

# ✅ PHASE 1 — Update Database Schema

## Step 1.1 — Add new Pomodoro-related columns

**File:** `schema.sql`

### Instructions:

1. Open `schema.sql`.
2. Locate the `CREATE TABLE lists` section.
3. Add the following columns inside the table definition:

   ```sql
   timer_state TEXT DEFAULT 'idle',
   timer_remaining INTEGER DEFAULT 0,
   sessions_completed INTEGER DEFAULT 0,
   timer_started_at TIMESTAMP
   ```
4. Save the file.

### Step 1.2 — Create migration (if necessary)

If database already exists:

1. Create a file named `manual_migration.sql`.
2. Insert:

   ```sql
   ALTER TABLE lists ADD COLUMN timer_state TEXT DEFAULT 'idle';
   ALTER TABLE lists ADD COLUMN timer_remaining INTEGER DEFAULT 0;
   ALTER TABLE lists ADD COLUMN sessions_completed INTEGER DEFAULT 0;
   ALTER TABLE lists ADD COLUMN timer_started_at TIMESTAMP;
   ```
3. Run manually in SQLite using terminal.

If OK to reset DB:

1. Run: `flask init-db`

---

# ✅ PHASE 2 — Create Backend Timer API

## Step 2.1 — Create new file

**File:** `routes/pomodoro.py`

### Instructions:

Create new file with EXACT contents:

```python
from flask import Blueprint, request, jsonify
from ..db import get_db
from datetime import datetime

bp = Blueprint('pomodoro', __name__, url_prefix='/timer')

# Helper function

def get_active_list(db):
    return db.execute('SELECT * FROM lists WHERE is_active = 1').fetchone()

@bp.route('/status')
def status():
    db = get_db()
    active = get_active_list(db)
    if not active:
        return jsonify({'error': 'No active list'}), 400

    # Calculate remaining time
    remaining = active['timer_remaining']
    if active['timer_state'] not in ('idle', 'paused') and active['timer_started_at']:
        started = datetime.fromisoformat(active['timer_started_at'])
        elapsed = (datetime.utcnow() - started).total_seconds()
        remaining = max(0, remaining - int(elapsed))

    return jsonify({
        'state': active['timer_state'],
        'remaining': remaining,
        'sessions_completed': active['sessions_completed'],
    })

@bp.route('/start', methods=['POST'])
def start():
    db = get_db()
    active = get_active_list(db)
    if not active:
        return jsonify({'error': 'No active list'}), 400

    # Determine duration based on state
    if active['timer_state'] in ('idle', 'long_break', 'short_break', 'session'):
        # SESSION START
        duration = active['pomo_session'] * 60
    elif active['timer_state'] == 'paused':
        duration = active['timer_remaining']

    # Set timer
    db.execute(
        'UPDATE lists SET timer_state = ?, timer_remaining = ?, timer_started_at = ? WHERE id = ?',
        ('session', duration, datetime.utcnow().isoformat(), active['id'])
    )
    db.commit()

    return jsonify({'state': 'session', 'remaining': duration})

@bp.route('/pause', methods=['POST'])
def pause():
    db = get_db()
    active = get_active_list(db)

    if not active or not active['timer_started_at']:
        return jsonify({'error': 'Cannot pause'}), 400

    started = datetime.fromisoformat(active['timer_started_at'])
    elapsed = int((datetime.utcnow() - started).total_seconds())
    remaining = max(0, active['timer_remaining'] - elapsed)

    db.execute(
        'UPDATE lists SET timer_state = ?, timer_remaining = ?, timer_started_at = NULL WHERE id = ?',
        ('paused', remaining, active['id'])
    )
    db.commit()

    return jsonify({'state': 'paused', 'remaining': remaining})

@bp.route('/reset', methods=['POST'])
def reset():
    db = get_db()
    active = get_active_list(db)

    db.execute(
        'UPDATE lists SET timer_state = ?, timer_remaining = 0, timer_started_at = NULL WHERE id = ?',
        ('idle', active['id'])
    )
    db.commit()

    return jsonify({'state': 'idle'})
```

---

## Step 2.2 — Register the Blueprint

**File:** `__init__.py`

### Instructions:

1. Add:

```python
from .routes import pomodoro
app.register_blueprint(pomodoro.bp)
```

Just below where other blueprints are registered.

---

# ✅ PHASE 3 — Create Timer UI

## Step 3.1 — Modify `templates/home/index.html`

### Instructions:

1. Find the Pomodoro placeholder.
2. Replace it with:

```html
<div id="pomodoro-container">
    <div class="timer-phase">Focus Session</div>
    <div class="timer-display">25:00</div>
    <div class="timer-progress"><div class="progress-bar"></div></div>

    <div class="timer-controls">
        <button id="startPauseBtn">Start</button>
        <button id="resetBtn">Reset</button>
        <button id="skipBtn">Skip</button>
    </div>
    <div class="timer-sessions">0/4 Sessions</div>
</div>
```

3. Ensure page includes:

```html
<script src="{{ url_for('static', filename='js/pomodoro.js') }}"></script>
```

---

# ✅ PHASE 4 — Create Timer JavaScript

## Step 4.1 — Create new JS file

**File:** `static/js/pomodoro.js`

### Instructions:

Paste EXACTLY:

```javascript
let remaining = 0;
let timerState = 'idle';
let timerInterval = null;

async function fetchStatus() {
    const res = await fetch('/timer/status');
    const data = await res.json();
    timerState = data.state;
    remaining = data.remaining;
    updateDisplay();
    if (timerState !== 'idle' && timerState !== 'paused') startCountdown();
}

function updateDisplay() {
    const minutes = String(Math.floor(remaining / 60)).padStart(2, '0');
    const seconds = String(remaining % 60).padStart(2, '0');
    document.querySelector('.timer-display').textContent = `${minutes}:${seconds}`;
}

function startCountdown() {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        remaining--;
        updateDisplay();
        if (remaining <= 0) clearInterval(timerInterval);
    }, 1000);
}

async function startTimer() {
    const res = await fetch('/timer/start', { method: 'POST' });
    const data = await res.json();
    timerState = data.state;
    remaining = data.remaining;
    startCountdown();
}

async function pauseTimer() {
    await fetch('/timer/pause', { method: 'POST' });
    clearInterval(timerInterval);
}

async function resetTimer() {
    await fetch('/timer/reset', { method: 'POST' });
    clearInterval(timerInterval);
    remaining = 0;
    updateDisplay();
}

document.getElementById('startPauseBtn').addEventListener('click', startTimer);
document.getElementById('resetBtn').addEventListener('click', resetTimer);

fetchStatus();
```

---

# ✅ PHASE 5 — Add Basic Styling

## Step 5.1 — Modify CSS

**File:** `static/css/style.css`

### Add at bottom:

```css
.timer-display {
    font-size: 4rem;
    text-align: center;
}

.timer-controls button {
    padding: 0.5rem 1rem;
    margin: 0.3rem;
}

.progress-bar {
    height: 8px;
    background: red;
    width: 0%;
}
```

---

# END OF DOCUMENT

This file can be executed step-by-step by any AI model to implement the Pomodoro system into your app.



