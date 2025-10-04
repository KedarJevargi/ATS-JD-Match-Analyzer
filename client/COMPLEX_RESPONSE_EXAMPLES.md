# Complex Response Examples

This document demonstrates how the `AnalysisResults` component handles different response formats.

## Response Format 1: String Suggestions (Legacy)

```typescript
{
  column: true,
  "simple fonts": true,
  "no images": true,
  "clear section header": true,
  "poor text alignment": false,
  "no tables": true,
  "key words matched": ["Python", "React", "TypeScript"],
  "keyword missing": ["Docker", "Kubernetes"],
  score: {
    "overall score": 85.5,
    "structure score": 90.0,
    "keyword score": 80.0
  },
  suggestions: "Consider adding Docker and Kubernetes to your skills section..."
}
```

**Rendering**: The string suggestion is displayed as plain text in a suggestion box.

---

## Response Format 2: Complex Object Suggestions (New)

```typescript
{
  column: true,
  "simple fonts": true,
  "no images": true,
  "clear section header": true,
  "poor text alignment": false,
  "no tables": true,
  "key words matched": ["Python", "React", "TypeScript"],
  "keyword missing": ["Docker", "Kubernetes"],
  score: {
    "overall score": 85.5,
    "structure score": 90.0,
    "keyword score": 80.0
  },
  suggestions: {
    structural_fixes: [
      "Remove images from header section",
      "Convert multi-column layout to single column",
      "Use standard fonts (Arial, Calibri, Times)"
    ],
    content_fixes: [
      "Add Python, Django, and RESTful APIs under 'Technical Skills'",
      "Mention CI/CD Pipelines and GitHub Actions under 'Projects'",
      "Include Docker and Kubernetes in the DevOps section"
    ],
    section_updates: {
      Summary: [
        "Highlight backend engineering experience",
        "Mention years of experience with specific technologies"
      ],
      Skills: [
        "Add: Docker, Kubernetes, AWS, microservices",
        "Reorganize by category: Languages, Frameworks, Tools"
      ],
      Experience: [
        "Quantify achievements with metrics",
        "Emphasize scalability and performance improvements"
      ],
      Projects: [
        "Add project demonstrating distributed systems knowledge",
        "Include links to GitHub repositories"
      ]
    },
    final_recommendations: [
      "Ensure all sections are ATS-friendly",
      "Use industry-standard keywords throughout",
      "Keep formatting simple and clean"
    ]
  }
}
```

**Rendering**: The complex object is broken down into organized sections:
- **Structural Fixes**: List of structural improvements
- **Content Fixes**: List of content-related changes
- **Section Updates**: Nested lists organized by resume section (Summary, Skills, Experience, Projects, Education)
- **Final Recommendations**: Summary of key recommendations

---

## Type Safety

The component uses TypeScript type guards to safely determine the type of suggestions:

```typescript
const isComplexSuggestions = (
  suggestions: string | ComplexSuggestions | undefined
): suggestions is ComplexSuggestions => {
  return typeof suggestions === 'object' && suggestions !== null;
};
```

This ensures:
- ✅ No runtime errors when accessing object properties
- ✅ Proper type inference in conditional branches
- ✅ Null/undefined safety
- ✅ No "Objects are not valid as a React child" errors

---

## Backend Response Structure

The backend returns:
```typescript
{
  result: AnalysisResult,
  response: string | ComplexSuggestions
}
```

The API service transforms this into:
```typescript
{
  ...result,
  suggestions: response
}
```

This allows the component to handle both legacy string responses and new structured object responses seamlessly.
