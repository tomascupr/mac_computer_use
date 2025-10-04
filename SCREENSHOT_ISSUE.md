# Critical Issue: Agent Working Blind - Screenshots Not Taken After Actions

## TL;DR
**The agent is NOT seeing the results of most of its actions.** Screenshots are only taken for `type` and explicit `screenshot` actions. All clicks, mouse moves, and key presses run **without visual feedback**, making the agent essentially guess what happened.

**This is why computer use feels random.**

---

## Current Screenshot Behavior

### ✅ Actions That Return Screenshots
1. **`type` action** - Takes screenshot AFTER typing (computer.py:209)
2. **`screenshot` action** - Explicitly takes screenshot (computer.py:230)

### ❌ Actions That DON'T Return Screenshots
1. **`mouse_move`** - No screenshot (computer.py:122)
2. **`left_click`** - No screenshot (computer.py:248)
3. **`right_click`** - No screenshot (computer.py:248)
4. **`double_click`** - No screenshot (computer.py:248)
5. **`middle_click`** - No screenshot (computer.py:248)
6. **`left_click_drag`** - No screenshot (computer.py:124)
7. **`key` (keyboard combinations)** - No screenshot (computer.py:184, 200)
8. **`cursor_position`** - No screenshot (computer.py:234)

---

## Code Evidence

### Type Action (HAS Screenshot)
```python
# tools/computer.py:204-214
elif action == "type":
    results: list[ToolResult] = []
    for chunk in chunks(text, TYPING_GROUP_SIZE):
        cmd = f"cliclick w:{TYPING_DELAY_MS} t:{shlex.quote(chunk)}"
        results.append(await self.shell(cmd, take_screenshot=False))  # ← No screenshot during typing
    screenshot_base64 = (await self.screenshot()).base64_image  # ← Screenshot AFTER typing
    return ToolResult(
        output="".join(result.output or "" for result in results),
        error="".join(result.error or "" for result in results),
        base64_image=screenshot_base64,  # ← Returns screenshot
    )
```

### Click Actions (NO Screenshot)
```python
# tools/computer.py:241-248
else:
    click_cmd = {
        "left_click": "c:.",
        "right_click": "rc:.",
        "middle_click": "mc:.",
        "double_click": "dc:.",
    }[action]
    return await self.shell(f"cliclick {click_cmd}")  # ← No take_screenshot parameter
```

### Mouse Move (NO Screenshot)
```python
# tools/computer.py:121-122
if action == "mouse_move":
    return await self.shell(f"cliclick m:{x},{y}")  # ← No take_screenshot parameter
```

### Key Press (NO Screenshot)
```python
# tools/computer.py:184
return await self.shell(cmd, take_screenshot=False)  # ← Explicitly disabled

# tools/computer.py:200
return ToolResult(output=f"Pressed key: {text}", error=None, base64_image=None)  # ← No image
```

---

## Why This Causes "Random" Behavior

### Example Scenario: Agent Tries to Click a Button

1. **Agent**: "I'll click at coordinates (500, 300)"
   - Executes: `left_click` at (500, 300)
   - Returns: `ToolResult(output="", error="", base64_image=None)`

2. **Agent receives**: Text saying action succeeded, but **NO VISUAL CONFIRMATION**

3. **Agent doesn't know:**
   - Did the button actually get clicked?
   - Did a menu open?
   - Did a dialog appear?
   - Did the page change?
   - Is the UI still loading?

4. **Agent guesses next step** based on assumption that click worked

5. **If the click didn't work** (wrong coordinates, UI lag, button disabled, etc.):
   - Agent continues with wrong assumptions
   - Makes more blind actions
   - Spirals into confusion
   - Appears "random" to the user

---

## How Vision Actually Works in Computer Use

Looking at the agentic loop (loop.py:164-180):

```python
for content_block in cast(list[BetaContentBlock], response.content):
    output_callback(content_block)
    if content_block.type == "tool_use":
        result = await tool_collection.run(
            name=content_block.name,
            tool_input=cast(dict[str, Any], content_block.input),
        )
        tool_result_content.append(
            _make_api_tool_result(result, content_block.id)
        )
```

The `_make_api_tool_result` function (loop.py:232-265) handles screenshots:

```python
def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []

    # ... error handling ...

    if result.base64_image:  # ← Only includes image if ToolResult has one
        tool_result_content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,  # ← Sends to API
                },
            }
        )
```

**If `result.base64_image` is `None` (which it is for most actions), the agent gets NO visual feedback.**

---

## Impact on Token Usage & Performance

### Current State (Broken)
- Agent clicks button → No screenshot
- Agent has to **guess** what happened
- Agent might request explicit screenshot to verify
- **Extra API calls** to compensate for lack of feedback
- **More errors** due to wrong assumptions

### If Fixed (Screenshots After Each Action)
- Agent clicks button → Gets screenshot
- Agent **sees** what happened
- Agent makes informed decision
- **Fewer API calls** (less guessing)
- **Better success rate** (informed actions)

**Paradox:** Taking screenshots after every action would actually REDUCE overall token usage because:
1. Fewer failed action sequences
2. No need for explicit screenshot requests
3. Agent can verify success immediately
4. Less backtracking and error recovery

---

## Comparison with Other Implementations

### Pydantic AI (Best Practice)
```python
@agent.tool_plain
def click_and_capture(x: int, y: int) -> ToolReturn:
    """Click at coordinates and show before/after screenshots."""
    before_screenshot = capture_screen()  # Before
    perform_click(x, y)
    time.sleep(0.5)  # Wait for UI update
    after_screenshot = capture_screen()   # After

    return ToolReturn(
        return_value=f"Successfully clicked at ({x}, {y})",
        content=[
            "Before:",
            BinaryContent(data=before_screenshot, media_type="image/png"),
            "After:",
            BinaryContent(data=after_screenshot, media_type="image/png"),
        ]
    )
```

**They provide BOTH before and after screenshots!** This gives the agent maximum context.

### Our Implementation (Broken)
```python
if action == "left_click":
    return await self.shell(f"cliclick c:.")  # ← Returns nothing
```

No screenshot, no visual feedback, agent is blind.

---

## Recommended Fix

### Option 1: Screenshots After ALL Actions (Recommended)

```python
async def __call__(self, *, action: Action, text: str | None = None, coordinate: tuple[int, int] | None = None, **kwargs):
    # ... existing code ...

    if action in ("mouse_move", "left_click_drag"):
        x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

        if action == "mouse_move":
            return await self.shell(f"cliclick m:{x},{y}", take_screenshot=True)  # ← ADD
        elif action == "left_click_drag":
            return await self.shell(f"cliclick dd:{x},{y}", take_screenshot=True)  # ← ADD

    # ... for click actions ...
    else:
        click_cmd = {
            "left_click": "c:.",
            "right_click": "rc:.",
            "middle_click": "mc:.",
            "double_click": "dc:.",
        }[action]
        return await self.shell(f"cliclick {click_cmd}", take_screenshot=True)  # ← ADD

    # ... for key actions ...
    if action == "key":
        # ... execute key press ...
        result = await self.shell(cmd, take_screenshot=True)  # ← CHANGE
        # Take screenshot after action completes
        screenshot_base64 = (await self.screenshot()).base64_image
        return result.replace(base64_image=screenshot_base64)
```

**Changes needed:**
1. Add `take_screenshot=True` to all `shell()` calls
2. For actions that don't use `shell()`, explicitly call `screenshot()` after action
3. Ensure screenshot is taken AFTER action completes (wait for UI to update)

### Option 2: Configurable Screenshot Behavior

```python
class ComputerTool(BaseAnthropicTool):
    _screenshot_after_actions: bool = True  # Make configurable

    async def __call__(self, ...):
        # ... execute action ...

        if self._screenshot_after_actions and action != "screenshot":
            result = await self.execute_action(...)
            screenshot = await self.screenshot()
            return result.replace(base64_image=screenshot.base64_image)
```

**Pros:**
- User can disable if needed (e.g., for cost optimization)
- Default is True (best UX)
- Easy to toggle

**Cons:**
- Added complexity
- Most users won't understand why to disable it

### Option 3: Selective Screenshots (Not Recommended)

Only take screenshots for "important" actions like clicks, not for mouse_move.

**Why this is bad:**
- Hard to define "important"
- Agent still blind for some actions
- Inconsistent behavior

---

## Implementation Checklist

- [ ] Update `mouse_move` to take screenshot
- [ ] Update `left_click` to take screenshot
- [ ] Update `right_click` to take screenshot
- [ ] Update `double_click` to take screenshot
- [ ] Update `middle_click` to take screenshot
- [ ] Update `left_click_drag` to take screenshot
- [ ] Update `key` action to take screenshot
- [ ] Test screenshot delay is sufficient (UI has time to update)
- [ ] Verify screenshots are properly base64 encoded
- [ ] Confirm screenshots are sent to API
- [ ] Test with real workflows (clicking, typing, navigating)
- [ ] Measure token usage impact
- [ ] Update documentation

---

## Performance Considerations

### Screenshot Delay
Current: `_screenshot_delay = 1.0` seconds

**Problem:** This might be too long or too short depending on the application
- Fast apps: 1s is wasteful
- Slow apps: 1s might not be enough for UI to update

**Solution:** Make adaptive based on action type
```python
_screenshot_delays = {
    "click": 0.3,      # UI usually responds fast
    "type": 0.5,       # Might have autocomplete
    "drag": 0.5,       # Animation might take time
    "mouse_move": 0.1, # No UI change expected
}
```

### Screenshot Size
Current: Scales to 1366x768 (FWXGA)

**This is good** - matches Anthropic's recommendations. No change needed.

### Token Cost
Each screenshot ≈ 1,500 tokens (for 1366x768 PNG)

**With screenshots after every action:**
- 10 actions = ~15,000 tokens
- But: Fewer failed sequences, fewer retries
- Net result: Likely **saves tokens** overall

---

## Testing Strategy

### Before Fix
1. Ask agent to "Click the X button"
2. Observe: Agent clicks, has no visual feedback
3. Observe: Agent might click again or get confused
4. Result: "Random" behavior

### After Fix
1. Ask agent to "Click the X button"
2. Agent clicks, sees result screenshot
3. Agent confirms action succeeded
4. Agent proceeds with informed next step
5. Result: Predictable behavior

### Test Cases
1. **Simple click**: Click button, verify screenshot shows clicked state
2. **Multi-step workflow**: Open menu → click item → verify each step has visual feedback
3. **Error recovery**: Click disabled button, agent should SEE it's disabled
4. **UI lag**: Click button with slow UI, verify screenshot delay is sufficient
5. **Token usage**: Compare total tokens before/after fix

---

## Why This Wasn't Caught Earlier

1. **Type action works** - Because it DOES take screenshots, basic testing passed
2. **Explicit screenshots work** - Agent can always request screenshot manually
3. **Short demos work** - Agent can compensate with extra screenshot requests
4. **Complex tasks fail** - Only becomes obvious with longer workflows

---

## Conclusion

**The agent is essentially blind for most actions.** This is a critical bug that makes computer use feel unreliable and random.

**Fix:** Enable screenshots after ALL actions by default.

**Expected improvement:**
- ✅ Agent makes informed decisions
- ✅ Fewer failed action sequences
- ✅ Better user experience
- ✅ Likely reduces overall token usage (fewer retries)
- ✅ Matches best practices (see Pydantic AI example)

**Priority:** 🔥 CRITICAL - This fundamentally breaks the computer use experience

---

## References
- Current implementation: `tools/computer.py`
- Agentic loop: `loop.py`
- Pydantic AI example: Shows screenshots before AND after actions
- Anthropic docs: Recommend XGA resolution, but don't specify screenshot frequency
