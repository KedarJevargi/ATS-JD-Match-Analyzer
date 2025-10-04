# Backend Fix: Parse Gemini Response to Structured JSON

## Problem
The backend's `/ats/analyse` endpoint was returning raw text from the Gemini API instead of a structured JSON object. The frontend was already prepared to handle complex objects with `structural_fixes`, `content_fixes`, `section_updates`, and `final_recommendations`, but it was receiving raw text instead.

## Solution
Updated `server/routers/ats_router.py` to parse the Gemini response text into a JSON object before returning it to the frontend.

## Changes Made

### 1. Updated the Prompt Template
- Changed the prompt to explicitly request a JSON response with a specific structure
- Added clear instructions: "Return ONLY a valid JSON object with this exact structure"
- Specified the exact JSON schema with all required keys
- Used capitalized section names (Summary, Skills, etc.) to match TypeScript type definitions

### 2. Added JSON Parsing Logic
```python
# Parse the response text into a JSON object
response_text = gemini_response.text.strip()

# Remove markdown code block formatting (e.g., ```json ... ```) if present
if response_text.startswith('```'):
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        response_text = response_text[start_idx:end_idx + 1]

# Try to parse as JSON, fall back to raw text if parsing fails
try:
    parsed_response = json.loads(response_text)
    return {
        "result": analysis_result_json,
        "response": parsed_response
    }
except json.JSONDecodeError:
    # If JSON parsing fails, return the raw text as fallback
    return {
        "result": analysis_result_json,
        "response": response_text
    }
```

## Expected Response Structure

### Before (Raw Text)
```json
{
  "result": { /* analysis data */ },
  "response": "Structural Fixes:\n- Fix 1\n- Fix 2\n\nContent Fixes:\n..."
}
```

### After (Structured JSON)
```json
{
  "result": { /* analysis data */ },
  "response": {
    "structural_fixes": [
      "Correct the poor text alignment identified in the analysis.",
      "Remove the '(cid:...)' artifacts throughout the document."
    ],
    "content_fixes": [
      "Add the keyword 'HTTP' to your 'Skills' section.",
      "Incorporate the keyword 'Collaboration' into your project descriptions."
    ],
    "section_updates": {
      "Summary": ["Your summary is strong but could be more concise."],
      "Skills": ["Move specific technologies into your main 'Skills' section."],
      "Projects": ["Correct the dates for your projects."],
      "Education": ["The education section is clear and well-structured."]
    },
    "final_recommendations": [
      "First, fix the structural issues.",
      "Second, enhance your content by adding relevant missing keywords.",
      "Third, update the dates for your projects."
    ]
  }
}
```

## Compatibility

### Backward Compatibility
The solution maintains backward compatibility by:
- Falling back to raw text if JSON parsing fails
- The frontend already has type guards to handle both string and object responses
- No breaking changes to the API contract

### Frontend Integration
The frontend components are already prepared to handle this structure:
- `client/src/types/api.ts` - Defines `ComplexSuggestions` interface
- `client/src/components/AnalysisResults.tsx` - Has rendering logic for complex objects
- `client/src/services/api.ts` - Preserves the response type

## Testing
- ✅ Python syntax validation passed
- ✅ JSON parsing logic tested with multiple scenarios
- ✅ Client build successful
- ✅ Linter passed with no warnings

## Benefits
1. **Better UX**: Frontend can now display suggestions in a structured, organized format
2. **Type Safety**: Frontend gets properly typed data matching TypeScript interfaces
3. **Maintainability**: Structured data is easier to work with and extend
4. **Graceful Degradation**: Falls back to text if parsing fails
5. **Consistency**: Matches the pattern used in `sendGemini.py` for parsing Gemini responses
