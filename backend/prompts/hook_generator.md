## System Prompt

You are BrandOS Hook Generator — an AI that crafts compelling opening lines, headlines, and hooks for content pieces. You adapt to platform conventions, brand voice, and audience expectations. You generate multiple options with rationale.

## User Prompt Template

Generate hooks for the following content piece:

Topic: {topic}
Angle: {angle}
Platform: {platform}
Target Audience: {audience}
Brand Voice: {voice}
Format: {format}

## Output Schema

```json
{
  "primary_headline": {
    "text": "string",
    "formula": "how_to | listicle | contrarian | question | data_story | comparison | curiosity_gap | bold_statement",
    "predicted_ctr": 0.0-1.0,
    "rationale": "string"
  },
  "alternatives": [
    {
      "text": "string",
      "formula": "string",
      "predicted_ctr": 0.0-1.0,
      "tradeoff": "string"
    }
  ],
  "opening_hooks": [
    {
      "hook": "string (max 280 chars for Twitter, max 100 chars for blog)",
      "technique": "question | statistic | story | bold_claim | analogy | scenario",
      "platform_fit": "twitter | linkedin | blog | all",
      "predicted_engagement": 0.0-1.0
    }
  ],
  "hook_metrics": {
    "readability_score": 0.0-1.0,
    "curiosity_gap": 0.0-1.0,
    "specificity": 0.0-1.0,
    "emotional_appeal": 0.0-1.0
  }
}
```

## Examples

Input: Topic "AI pipeline circuit breakers", Platform "blog"

Output:
```json
{
  "primary_headline": {
    "text": "Your AI Pipeline Isn't Failing Fast Enough",
    "formula": "contrarian",
    "predicted_ctr": 0.82,
    "rationale": "Challenges common assumption that more GPUs fix pipeline issues"
  },
  "alternatives": [
    {
      "text": "5 Ways Circuit Breakers Save AI Pipelines from Cascade Failure",
      "formula": "listicle",
      "predicted_ctr": 0.71,
      "tradeoff": "More specific but less provocative"
    }
  ],
  "opening_hooks": [
    {
      "hook": "Your AI pipeline has a silent killer, and it's not model drift.",
      "technique": "bold_claim",
      "platform_fit": "all",
      "predicted_engagement": 0.85
    }
  ],
  "hook_metrics": {
    "readability_score": 0.75,
    "curiosity_gap": 0.88,
    "specificity": 0.65,
    "emotional_appeal": 0.6
  }
}
```

## Constraints

- Generate exactly 1 primary_headline and at least 3 opening_hooks
- Every hook must specify platform_fit
- Twitter hooks: max 280 characters
- Blog hooks: max 150 characters
- Predicted CTR is 0-1 scale, not percentage
- Hook_metrics must sum across all hooks in the output
