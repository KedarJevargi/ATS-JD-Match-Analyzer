# Component Structure Visualization

## AnalysisResults Component Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      AnalysisResults                            │
│                                                                 │
│  Props: { results: AnalysisResult }                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │   results.suggestions exists?             │
        └────────────┬──────────────────────────────┘
                     │
           ┌─────────┴──────────┐
           │                    │
           ▼                    ▼
    [String Type]        [Object Type]
           │                    │
           │              ┌─────┴─────────────────────┐
           │              │ isComplexSuggestions()    │
           │              │ Type Guard Check          │
           │              └─────┬─────────────────────┘
           │                    │
           │                    ▼
           │         ┌──────────────────────────────────┐
           │         │  renderComplexSuggestions()      │
           │         └──────────────────────────────────┘
           │                    │
           │         ┌──────────┼──────────┐
           │         │          │          │
           │         ▼          ▼          ▼
           │    [struct_]  [content_] [section_]  [final_]
           │    [fixes]    [fixes]    [updates]   [recom.]
           │         │          │          │          │
           │         ▼          ▼          ▼          ▼
           │    renderStringList()  renderSectionUpdates()
           │         │          │          │          │
           │         └──────────┴──────────┴──────────┘
           │                    │
           │         ┌──────────▼──────────┐
           │         │ Complex UI Elements │
           │         │ • Subsections       │
           │         │ • Bullet Lists      │
           │         │ • Nested Cards      │
           │         └─────────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ <p> Simple Text  │
    │ String Display   │
    └──────────────────┘
```

## Type Hierarchy

```
AnalysisResult
├── column: boolean
├── simple fonts: boolean
├── no images: boolean
├── clear section header: boolean
├── poor text alignment: boolean
├── no tables: boolean
├── key words matched: string[]
├── keyword missing: string[]
├── score: AnalysisScore
│   ├── overall score: number
│   ├── structure score: number
│   └── keyword score: number
└── suggestions?: string | ComplexSuggestions
                          │
                          └─ ComplexSuggestions
                              ├── structural_fixes?: string[]
                              ├── content_fixes?: string[]
                              ├── section_updates?: SectionUpdates
                              │   ├── Summary?: string[]
                              │   ├── Skills?: string[]
                              │   ├── Experience?: string[]
                              │   ├── Projects?: string[]
                              │   └── Education?: string[]
                              └── final_recommendations?: string[]
```

## Rendering Logic Flow

```
Input: results.suggestions
  │
  ├─ undefined/null ──────────────────────────► (render nothing)
  │
  ├─ typeof string ───────────────────────────► <p>{suggestions}</p>
  │
  └─ typeof object ──────────────────────────┐
                                             │
                                             ▼
                            ┌────────────────────────────────┐
                            │ renderComplexSuggestions()     │
                            └────────────────────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
         ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
         │ structural_fixes │   │ content_fixes    │   │ final_recomm.    │
         │                  │   │                  │   │                  │
         │ if (!empty)      │   │ if (!empty)      │   │ if (!empty)      │
         │   render list    │   │   render list    │   │   render list    │
         └──────────────────┘   └──────────────────┘   └──────────────────┘
                    │
                    └─► <div className="suggestion-subsection">
                          <h4>{title}</h4>
                          <ul className="suggestion-list">
                            <li>{item}</li>
                            ...
                          </ul>
                        </div>

                    ┌──────────────────┐
                    │ section_updates  │
                    │                  │
                    │ if (!empty)      │
                    │   renderSection  │
                    │   Updates()      │
                    └────────┬─────────┘
                             │
                             ▼
                    for each section (Summary, Skills, etc):
                      <div className="section-update">
                        <h5>{sectionName}</h5>
                        <ul>
                          <li>{update}</li>
                          ...
                        </ul>
                      </div>
```

## CSS Class Structure

```
.suggestions-box
  └── .complex-suggestions
      ├── .suggestion-subsection
      │   ├── .subsection-title
      │   └── .suggestion-list
      │       └── li (with ::before pseudo-element)
      │
      └── .suggestion-subsection (for section_updates)
          ├── .subsection-title
          └── .section-update (repeated for each section)
              ├── .section-name
              └── .suggestion-list
                  └── li (with ::before pseudo-element)
```

## Error Prevention

**Before Fix:**
```typescript
<p>{results.suggestions}</p>
// ERROR if suggestions is an object:
// "Objects are not valid as a React child"
```

**After Fix:**
```typescript
{isComplexSuggestions(results.suggestions) ? (
  renderComplexSuggestions(results.suggestions)  // ✅ Safe
) : (
  <p>{results.suggestions}</p>  // ✅ Safe
)}
```

## Type Safety Chain

```
1. Backend Response
   ↓ (typed as string | object)
2. API Service
   ↓ (preserves type, returns AnalysisResult)
3. Component Props
   ↓ (typed as suggestions?: string | ComplexSuggestions)
4. Type Guard (isComplexSuggestions)
   ↓ (narrows type in conditional branches)
5. Rendering Functions
   ↓ (receives correctly typed parameters)
6. React Elements
   ✅ (only valid React children rendered)
```
