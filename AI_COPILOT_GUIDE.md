# 🤖 ResiPlan Copilot - AI Advisory Chat

## Overview

The Streamlit dashboard now includes an intelligent AI assistant in the sidebar that provides context-aware scheduling advice.

---

## Features

### 1. **Context-Aware Responses**
The Copilot automatically knows:
- Total number of interns in your program
- Current bottlenecks and capacity issues
- Critical stations requiring attention
- Your schedule's overall health

### 2. **Smart Keyword Recognition**
Ask natural questions and get relevant answers:

**Bottleneck Analysis:**
- "What bottlenecks do I have?"
- "Show me capacity problems"
- "Which stations have issues?"

**Month-Specific Queries:**
- "What's wrong with July?"
- "Check June assignments"
- "When should Stage A happen?"

**Optimization Help:**
- "How can I improve my schedule?"
- "What should I do about errors?"
- "Give me optimization tips"

**Constraint Explanations:**
- "What are the rules?"
- "Explain constraints"
- "What requirements must I meet?"

**General Assistance:**
- "What can you do?"
- "Help me troubleshoot"
- "How do I assign interns?"

### 3. **Interactive Chat Interface**
- Scrollable chat history (300px height)
- User messages on the right
- AI responses on the left
- Clear chat button (🗑️) to start fresh
- Welcome message on first load

---

## How It Works

### Context Building
Before responding, the Copilot analyzes:

```python
context = {
    'total_interns': len(st.session_state.interns),
    'bottleneck_count': analysis['bottlenecks_found'],
    'critical_stations': ['Labor Ward', 'Gynecology A', ...]
}
```

### Mock AI Engine (Hackathon Version)
- **No API calls** - works offline, no keys needed
- **Keyword-based** - pattern matching for smart responses
- **Contextual** - incorporates live data from your schedule
- **Extensible** - easy to swap in real LLM later

### Response Categories

The Copilot handles 10+ intent categories:
1. **Help/Capabilities** - What can you do?
2. **Bottlenecks** - Show capacity issues
3. **Months** - Month-specific analysis
4. **Interns** - Resident management
5. **Capacity** - Staffing problems
6. **Constraints** - Rule explanations
7. **Optimization** - Improvement tips
8. **Errors** - Troubleshooting
9. **Gratitude** - Thank you responses
10. **Default** - General clarification

---

## Example Conversations

### Conversation 1: Bottleneck Check
**User:** "What bottlenecks do I have?"

**Copilot:**
```
🔴 Critical Capacity Issues Detected

Based on current analysis, I see bottlenecks in:
- Labor Ward, Gynecology A, HRP Department

Recommended Actions:
1. Run the AI Scheduler to automatically rebalance assignments
2. Check the "Analytics & Bottlenecks" tab for detailed breakdown
3. Consider extending rotation durations or adjusting start dates

Would you like specific suggestions for any station?
```

### Conversation 2: Month Analysis
**User:** "Why is June problematic?"

**Copilot:**
```
📅 June Analysis

Common issues in June:
- Stage A exams (June only) - ensure Basic Sciences completed
- Vacation conflicts - verify leave schedules
- Capacity crunches - check staffing minimums

Quick Fix:
1. Go to "Interactive Editor" tab
2. Review June column
3. Manually adjust assignments if needed
4. Click "Apply Edits" to save

Check the "God View" tab for visual timeline!
```

### Conversation 3: Optimization
**User:** "How can I improve my schedule?"

**Copilot:**
```
💡 Optimization Strategies

For your 40-intern program:

Immediate Actions:
1. Run "🚀 AI Scheduler" (uses OR-Tools constraint solver)
2. Set time limit 300+ seconds for better solutions
3. Check "Analytics & Bottlenecks" tab for red flags

Manual Tuning:
- Use "Interactive Editor" to fine-tune AI results
- Focus on months with critical issues first
- Verify Stage A/B timing compliance

Advanced:
- If solver fails, it automatically relaxes capacity constraints
- Export PDF audit report for documentation
- Review bottleneck forecast to prevent future issues
```

---

## UI Location

The Copilot appears at the **bottom of the sidebar**, below:
1. Configuration settings
2. Load Data button
3. Run AI Scheduler button
4. Statistics (Total Interns, Model A/B)

This placement ensures:
- Always visible
- Doesn't interfere with primary controls
- Easy access during analysis

---

## Technical Implementation

### Session State
```python
st.session_state.messages = [
    {"role": "user", "content": "What bottlenecks?"},
    {"role": "assistant", "content": "I see 3 critical..."}
]
```

### Mock Response Function
```python
def get_ai_response(user_input, context):
    """Returns smart responses based on keywords and context"""
    # Keyword matching
    # Context injection
    # Smart formatting
    return formatted_response
```

### Chat UI Components
```python
st.chat_input()  # User input box
st.chat_message() # Message bubbles
st.container()    # Scrollable history
```

---

## Upgrading to Real AI (Post-Hackathon)

To replace the mock with a real LLM:

### Option 1: Google Generative AI (Already in stack)
```python
import google.generativeai as genai

def get_ai_response(user_input, context):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""You are ResiPlan Copilot. Context: {context}
    User: {user_input}
    Provide scheduling advice."""
    response = model.generate_content(prompt)
    return response.text
```

### Option 2: OpenAI GPT
```python
from openai import OpenAI

def get_ai_response(user_input, context):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content
```

### Option 3: Local LLM (Ollama)
```python
import requests

def get_ai_response(user_input, context):
    response = requests.post('http://localhost:11434/api/generate',
        json={
            "model": "llama2",
            "prompt": f"Context: {context}\nUser: {user_input}"
        })
    return response.json()['response']
```

---

## Advantages of Mock Approach

For hackathon/demo:
- ✅ **No API costs** - completely free
- ✅ **No rate limits** - unlimited queries
- ✅ **Fast responses** - instant, no latency
- ✅ **Predictable** - same input = same output
- ✅ **Offline** - works without internet
- ✅ **No API keys** - no setup complexity

The mock is smart enough for:
- Live demos
- User testing
- Feature validation
- MVP presentation

---

## Future Enhancements

Potential additions:
- [ ] **Multi-turn conversations** - remember context across messages
- [ ] **Suggested questions** - quick action buttons
- [ ] **Voice input** - speech-to-text
- [ ] **Export chat** - save conversation as PDF
- [ ] **Proactive alerts** - AI notifies about issues
- [ ] **Natural language scheduling** - "Move Intern X to July"
- [ ] **Visualization generation** - "Show me a chart of..."

---

## Best Practices for Users

### Do Ask:
- ✅ "What issues do I have?"
- ✅ "Explain Stage A timing"
- ✅ "How to fix understaffing?"
- ✅ "What does this error mean?"

### Don't Ask (Yet):
- ❌ Very specific intern names (not indexed yet)
- ❌ Complex multi-step workflows
- ❌ Code-level debugging
- ❌ External system integrations

---

## Performance

- **Response time:** < 50ms (instant)
- **Context size:** ~500 chars
- **Message history:** Unlimited (stored in session)
- **Memory usage:** Minimal (~1KB per message)

---

## Accessibility

- Clear button for quick reset
- Welcome message guides first interaction
- Scrollable history for long conversations
- Readable font sizes
- Color contrast compliant

---

**Enjoy your new AI assistant! 🎉**

Perfect for:
- Live demos
- User walkthroughs
- Quick assistance
- Contextual help

