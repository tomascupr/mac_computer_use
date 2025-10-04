# Second Critical Issue: Agent Not Told to Analyze Screenshots

## TL;DR

Even when screenshots ARE sent, **Claude isn't explicitly instructed to analyze them**. The system prompt lacks guidance on:
1. Evaluating action outcomes from screenshots
2. Showing reasoning about visual feedback
3. Verifying if goals were achieved

This compounds the first issue (missing screenshots) and explains why computer use feels unreliable.

---

## What Anthropic Recommends

From official Computer Use documentation:

> **"After each step, take a screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking: 'I have evaluated step X...' If not correct, try again."**

Key insight:

> **"Claude sometimes assumes outcomes of its actions without explicitly checking their results."**

---

## Current System Prompt (loop.py:67-101)

```python
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilizing a macOS Sonoma 15.7 environment using {platform.machine()} architecture with command line internet access.
* Package management:
  - Use homebrew for package installation
  - Use curl for HTTP requests
  - Use npm/yarn for Node.js packages
  - Use pip for Python packages

* Browser automation available via Playwright:
  - Supports Chrome, Firefox, and WebKit
  - Can handle JavaScript-heavy applications
  - Capable of screenshots, navigation, and interaction
  - Handles dynamic content loading

* System automation:
  - cliclick for simulating mouse/keyboard input
  - osascript for AppleScript commands
  - launchctl for managing services
  - defaults for reading/writing system preferences

* Development tools:
  - Standard Unix/Linux command line utilities
  - Git for version control
  - Docker for containerization
  - Common build tools (make, cmake, etc.)

* Output handling:
  - For large output, redirect to tmp files: command > /tmp/output.txt
  - Use grep with context: grep -n -B <before> -A <after> <query> <filename>
  - Stream processing with awk, sed, and other text utilities

* Note: Command line function calls may have latency. Chain multiple operations into single requests where feasible.

* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>"""
```

### What's Missing

**NO guidance on:**
- ❌ Taking screenshots after actions
- ❌ Analyzing screenshot content
- ❌ Evaluating if actions succeeded
- ❌ Showing reasoning about visual feedback
- ❌ Verifying outcomes match expectations

---

## Recommended System Prompt Addition

### Option 1: Anthropic's Exact Guidance

```python
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
[... existing content ...]
</SYSTEM_CAPABILITY>

<IMPORTANT_VISUAL_FEEDBACK>
* After each computer use action (clicks, typing, keyboard shortcuts), a screenshot is automatically captured.
* You MUST carefully evaluate the screenshot to verify if your action achieved the intended outcome.
* Explicitly show your reasoning: "I have evaluated the screenshot after clicking X, and I can see that Y happened."
* If the outcome is not correct, try a different approach.
* Do NOT assume your actions succeeded - always verify by analyzing the screenshot.
* Pay close attention to:
  - Did the UI element you clicked respond?
  - Did a new window/dialog/menu appear?
  - Did the page/content change as expected?
  - Are there any error messages visible?
  - Is the application still loading/processing?
</IMPORTANT_VISUAL_FEEDBACK>"""
```

### Option 2: More Detailed Guidance

```python
SCREENSHOT_ANALYSIS_GUIDANCE = """
<SCREENSHOT_ANALYSIS>
* Every computer action returns a screenshot showing the result.
* You must analyze each screenshot before proceeding to the next action.
* Describe what you see: "The screenshot shows [description]"
* Verify success: "This confirms that [action] succeeded because [observation]"
* If unexpected: "The screenshot shows [unexpected result], so I will try [alternative approach]"

Examples of good analysis:
✅ "After clicking the File menu, the screenshot shows a dropdown menu with options including 'New', 'Open', and 'Save'. This confirms the menu opened successfully."
✅ "After typing the search term, I can see it appeared in the search box. However, no results are shown yet, so I'll press Enter to submit."
✅ "The button I clicked appears to still be in its default state - the screenshot shows no change. This suggests the click may not have registered. I'll try clicking again."

Examples of poor analysis:
❌ "Clicked the button." (No verification)
❌ "The menu should now be open." (Assumption, not observation)
❌ "Proceeding to next step." (No screenshot analysis)
</SCREENSHOT_ANALYSIS>

<VERIFICATION_CHECKLIST>
After each action, verify:
1. Visual state changed as expected (colors, positions, text)
2. No error messages appeared
3. Loading indicators completed (if any)
4. Target element is in expected state (selected, focused, etc.)
5. New UI elements appeared/disappeared as intended
</VERIFICATION_CHECKLIST>
"""
```

### Option 3: Minimal (for performance)

```python
MINIMAL_GUIDANCE = """
<IMPORTANT>
* Screenshots are captured after each action - analyze them before continuing.
* Explicitly state what you observe: "The screenshot shows..."
* Verify your actions succeeded before proceeding.
* If something unexpected appears, adjust your approach.
</IMPORTANT>
"""
```

---

## How This Affects Behavior

### Without Screenshot Analysis Guidance (Current)

```
Agent: "I'll click the submit button at (500, 300)"
→ [Screenshot taken but not explicitly analyzed]
Agent: "Now I'll navigate to the results page"
→ [Assumes click worked, doesn't verify]
→ [Actually, button didn't click - wrong coordinates]
→ [Agent continues with wrong assumptions]
→ [Task fails]
```

### With Screenshot Analysis Guidance (Recommended)

```
Agent: "I'll click the submit button at (500, 300)"
→ [Screenshot taken]
Agent: "Looking at the screenshot, I can see the submit button is still in its default state and no form submission occurred. The click may have missed the button. Let me try clicking again at slightly different coordinates."
→ [Adjusts approach based on visual feedback]
→ [Successfully clicks button]
Agent: "The screenshot now shows a loading indicator, confirming the form is being submitted. I'll wait for it to complete."
→ [Task succeeds]
```

---

## Evidence from Anthropic Docs

### Computer Use Best Practices

From the official documentation:

1. **Prompt Claude to evaluate screenshots:**
   > "After each step, take a screenshot and carefully evaluate if you have achieved the right outcome."

2. **Show reasoning explicitly:**
   > "Explicitly show your thinking: 'I have evaluated step X...'"

3. **Verify assumptions:**
   > "Claude sometimes assumes outcomes of its actions without explicitly checking their results."

4. **Use thinking feature (Claude 3.7+):**
   > "The thinking feature can help provide more insight into the model's reasoning process when interpreting screenshots and actions."

---

## Commented Out System Prompt (loop.py:53-66)

Interestingly, there WAS better guidance in the commented out prompt:

```python
# Line 57: "GUI apps will appear natively within macOS, but they may take some
# time to appear. Take a screenshot to confirm it did."
```

This explicitly told Claude to:
- Take a screenshot
- Confirm the action worked

**Why was this removed?**

The new prompt (lines 67-101) completely lacks this guidance. This is a regression.

---

## Combined Impact of Both Issues

### Issue #1: Screenshots Not Taken
Most actions don't capture screenshots at all.

### Issue #2: Screenshots Not Analyzed
Even when screenshots exist, Claude doesn't analyze them.

**Together, these make computer use effectively non-functional for complex tasks.**

---

## Implementation Recommendations

### Priority 1: Fix Screenshot Capture (Issue #1)
Add `take_screenshot=True` to all computer actions.

### Priority 2: Add Analysis Guidance (Issue #2)
Update system prompt to explicitly instruct screenshot analysis.

### Priority 3: Test Combined Fix
Verify that:
1. Screenshots are taken after every action ✓
2. Claude analyzes each screenshot ✓
3. Claude adjusts based on visual feedback ✓
4. Tasks complete successfully ✓

---

## Proposed Complete Fix

### 1. Update computer.py (from SCREENSHOT_ISSUE.md)
```python
# Add take_screenshot=True to all actions
return await self.shell(f"cliclick {click_cmd}", take_screenshot=True)
```

### 2. Update loop.py System Prompt
```python
SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilizing a macOS Sonoma 15.7 environment using {platform.machine()} architecture with command line internet access.

[... existing capabilities ...]

* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<SCREENSHOT_VERIFICATION>
* Every computer action automatically captures a screenshot showing the result.
* ALWAYS analyze the screenshot before proceeding to verify your action succeeded.
* Explicitly state what you observe: "The screenshot shows [description of what you see]"
* Verify the action's outcome: "This confirms [action] succeeded because [observation]"
* If something unexpected happened, describe it and adjust your approach.
* Pay attention to:
  - Did the UI element respond as expected?
  - Are there new windows, dialogs, or menus?
  - Did the content/page change correctly?
  - Are there any error messages?
  - Is anything still loading?
</SCREENSHOT_VERIFICATION>

<IMPORTANT>
* Do NOT assume actions succeeded - verify by analyzing the screenshot.
* If a screenshot shows your action didn't work, try a different approach.
* GUI applications may take time to appear - take a screenshot to confirm they launched.
</IMPORTANT>"""
```

### 3. Enable Thinking (for Claude 3.7+)
```python
# In loop.py sampling_loop
raw_response = client.beta.messages.with_raw_response.create(
    max_tokens=max_tokens,
    messages=messages,
    model=model,
    system=system,
    tools=tool_collection.to_params(),
    betas=[BETA_FLAG],
    thinking={  # ← Add this for Claude 3.7+
        "type": "enabled",
        "budget_tokens": 2000
    }
)
```

---

## Expected Improvements

### Before Fixes
- ❌ Screenshots not taken for most actions
- ❌ No explicit analysis when screenshots exist
- ❌ Agent assumes actions succeeded
- ❌ Lots of failed task sequences
- ❌ "Random" behavior

### After Fixes
- ✅ Screenshots taken after every action
- ✅ Claude analyzes each screenshot
- ✅ Claude verifies actions succeeded
- ✅ Adjusts approach when actions fail
- ✅ Predictable, reliable behavior

### Measurable Impact
- **Task success rate:** ~30% → ~80%+ (estimated)
- **API calls per task:** Fewer (less backtracking)
- **User satisfaction:** Significantly higher
- **Token usage:** Slightly higher per action, but lower overall (fewer retries)

---

## Testing Strategy

### Test 1: Simple Click with Analysis
**Without fix:**
```
User: "Click the OK button"
Agent: "Clicking OK button at (500, 300)"
Agent: "Proceeding to next step"  ← No verification
```

**With fix:**
```
User: "Click the OK button"
Agent: "Clicking OK button at (500, 300)"
Agent: "Analyzing the screenshot: I can see the dialog has closed and we're back to the main window. This confirms the OK button was clicked successfully."  ← Verified!
```

### Test 2: Failed Action Recovery
**Without fix:**
```
Agent: *clicks wrong coordinates*
Agent: *assumes it worked*
Agent: *continues with wrong state*
Agent: *fails completely*
```

**With fix:**
```
Agent: *clicks wrong coordinates*
Agent: "The screenshot shows the button is still visible and in its default state. My click didn't register. Let me try again with adjusted coordinates."
Agent: *tries again successfully*
```

### Test 3: UI Lag Handling
**Without fix:**
```
Agent: *clicks button*
Agent: *assumes menu opened*
Agent: *tries to click menu item that isn't there yet*
Agent: *fails*
```

**With fix:**
```
Agent: *clicks button*
Agent: "The screenshot shows the application is loading (I can see a spinner). I'll wait a moment for the UI to update."
Agent: *takes another screenshot*
Agent: "Now I can see the menu has appeared. I'll proceed to click the menu item."
```

---

## References

- **Anthropic Docs:** "After each step, take a screenshot and carefully evaluate if you have achieved the right outcome"
- **Current system prompt:** loop.py:67-101 (missing this guidance)
- **Commented prompt:** loop.py:53-66 (had better guidance, but removed)
- **Issue #1:** SCREENSHOT_ISSUE.md (screenshots not taken)
- **Issue #2:** This document (screenshots not analyzed)

---

## Conclusion

**Two critical issues are preventing effective computer use:**

1. **Screenshots not captured** for most actions → Agent is blind
2. **Screenshots not analyzed** when they exist → Agent doesn't verify

**Both must be fixed for computer use to work reliably.**

The good news: Both are straightforward to fix.
- Fix #1: Add `take_screenshot=True` to actions
- Fix #2: Add analysis guidance to system prompt

**Priority:** 🔥 CRITICAL - This breaks the entire computer use experience
