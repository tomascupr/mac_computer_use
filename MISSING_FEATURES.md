# Missing Features from Computer Use API 2025-01-24

## Summary
While the main computer tool has been updated to `computer_20250124`, several companion tools and new actions are still missing.

---

## ✅ Already Correct

### Beta Header (loop.py:27)
```python
BETA_FLAG = "computer-use-2025-01-24"  # ✅ Correct
```

### Computer Tool API Version (tools/computer.py:74)
```python
api_type: Literal["computer_20250124"] = "computer_20250124"  # ✅ Correct
```

---

## ❌ Need Updates

### 1. Bash Tool - Outdated API Version
**File:** `tools/bash.py`

**Current:**
```python
from anthropic.types.beta import BetaToolBash20241022Param
api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"

def to_params(self) -> BetaToolBash20241022Param:
    return {
        "type": self.api_type,
        "name": self.name,
    }
```

**Should be:**
```python
from anthropic.types.beta import BetaToolBash20250124Param
api_type: ClassVar[Literal["bash_20250124"]] = "bash_20250124"

def to_params(self) -> BetaToolBash20250124Param:
    return {
        "type": self.api_type,
        "name": self.name,
    }
```

**Lines to change:**
- Line 5: Import statement
- Line 114: api_type declaration
- Line 140: Return type annotation

---

### 2. Edit Tool - Outdated API Version
**File:** `tools/edit.py`

**Current:**
```python
from anthropic.types.beta import BetaToolTextEditor20241022Param
api_type: Literal["text_editor_20241022"] = "text_editor_20241022"

def to_params(self) -> BetaToolTextEditor20241022Param:
    return {
        "name": self.name,
        "type": self.api_type,
    }
```

**Should be:**
```python
from anthropic.types.beta import BetaToolTextEditor20250124Param
api_type: Literal["text_editor_20250124"] = "text_editor_20250124"

def to_params(self) -> BetaToolTextEditor20250124Param:
    return {
        "name": self.name,
        "type": self.api_type,
    }
```

**Lines to change:**
- Line 5: Import statement
- Line 26: api_type declaration
- Line 35: Return type annotation

---

## ❌ Missing New Computer Actions

### New Actions Available in computer_20250124

The following actions are supported by the new API but not implemented:

#### 1. `scroll` - Scroll with Direction Control
```python
# Expected parameters:
{
    "action": "scroll",
    "direction": "up" | "down" | "left" | "right",
    "amount": int  # Number of scroll units
}
```

**Implementation needed:**
```python
# In tools/computer.py Action literal (line 22):
Action = Literal[
    # ... existing actions ...
    "scroll",  # ← Add this
]

# In tools/computer.py __call__ method:
if action == "scroll":
    direction = kwargs.get("direction")  # up, down, left, right
    amount = kwargs.get("amount", 5)

    # cliclick scroll implementation
    # Note: This may need custom implementation as cliclick
    # doesn't have native scroll support
```

#### 2. `triple_click` - Triple Click Action
```python
# In Action literal:
"triple_click",

# In __call__ method (add to click actions section):
elif action == "triple_click":
    # cliclick doesn't have native triple-click
    # Need to implement as 3 rapid clicks
    return await self.shell("cliclick c:. c:. c:.")
```

#### 3. `left_mouse_down` / `left_mouse_up` - Granular Mouse Control
```python
# In Action literal:
"left_mouse_down",
"left_mouse_up",

# In __call__ method:
elif action == "left_mouse_down":
    return await self.shell("cliclick kd:lmb")  # Hold left mouse button
elif action == "left_mouse_up":
    return await self.shell("cliclick ku:lmb")  # Release left mouse button
```

#### 4. `hold_key` - Hold Key Down
```python
# Expected parameters:
{
    "action": "hold_key",
    "key": str,  # Key to hold
    "duration": float  # Seconds to hold
}

# In Action literal:
"hold_key",

# In __call__ method:
elif action == "hold_key":
    key = text
    duration = kwargs.get("duration", 1.0)

    # Implementation:
    # 1. Press key down
    # 2. Wait duration
    # 3. Release key
    await self.shell(f"cliclick kd:{key}")
    await asyncio.sleep(duration)
    await self.shell(f"cliclick ku:{key}")
```

#### 5. `wait` - Explicit Pause Between Actions
```python
# Expected parameters:
{
    "action": "wait",
    "duration": float  # Seconds to wait
}

# In Action literal:
"wait",

# In __call__ method:
elif action == "wait":
    duration = kwargs.get("duration", 1.0)
    await asyncio.sleep(duration)
    return ToolResult(output=f"Waited {duration} seconds", error=None, base64_image=None)
```

---

## Implementation Priority

### High Priority (Breaking Compatibility)
1. ✅ Update bash tool API version - **CRITICAL**
2. ✅ Update edit tool API version - **CRITICAL**

### Medium Priority (Enhanced Functionality)
3. ⚠️ Add `scroll` action - **Useful for web browsing**
4. ⚠️ Add `triple_click` action - **Text selection**
5. ⚠️ Add `wait` action - **Explicit timing control**

### Low Priority (Advanced Use Cases)
6. ⬜ Add `left_mouse_down`/`left_mouse_up` - **Drag operations**
7. ⬜ Add `hold_key` - **Gaming/special inputs**

---

## cliclick Command Reference

For implementing the new actions, here are the relevant cliclick commands:

```bash
# Mouse button control
cliclick kd:lmb    # Mouse button down
cliclick ku:lmb    # Mouse button up

# Key control
cliclick kd:cmd    # Key down
cliclick ku:cmd    # Key up

# Wait/delay
cliclick w:1000    # Wait 1000ms

# Multiple clicks
cliclick c:. c:. c:.  # Triple click at current position
```

**Note:** cliclick does not have native scroll support. Scrolling would need to be implemented using:
- Keyboard shortcuts (Page Up/Down, arrow keys)
- Mouse wheel events (complex, may need AppleScript)
- Alternative tool integration

---

## Testing Checklist

After implementing updates:

- [ ] Test bash tool with updated API version
- [ ] Test edit tool with updated API version
- [ ] Verify all existing computer actions still work
- [ ] Test new actions (scroll, triple_click, wait, etc.)
- [ ] Test with actual Claude API calls
- [ ] Check error handling for new actions
- [ ] Verify beta header compatibility

---

## Related Documentation

- [Anthropic Computer Use Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/computer-use-tool)
- [cliclick GitHub](https://github.com/BlueM/cliclick)
- Current implementation: `tools/computer.py`
- Loop handler: `loop.py`

---

## Recommendations

1. **Immediate:** Update bash and edit tools to 20250124 versions
2. **Short-term:** Add `scroll`, `triple_click`, and `wait` actions
3. **Long-term:** Consider implementing custom scroll mechanism or using alternative tools
4. **Testing:** Create comprehensive test suite for all actions

The most critical issue is that bash and edit tools are using outdated API versions, which could cause compatibility issues with the updated computer tool and beta flag.
