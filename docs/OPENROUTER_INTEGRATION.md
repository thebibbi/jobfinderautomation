# OpenRouter Integration Guide

## Overview

The job automation system now supports **OpenRouter**, a unified API gateway that provides access to 100+ AI models from multiple providers through a single interface. This dramatically improves the system's flexibility, cost-efficiency, and reliability.

## Why OpenRouter?

### 1. **Cost Optimization** (Save 50-90% on API costs)
- Use cheap models ($0.10/M tokens) for prescreening
- Reserve expensive models ($15/M tokens) for final analysis
- Mix and match models based on task complexity

### 2. **Model Diversity**
- Access Claude, GPT-4, Gemini, Llama, Mistral, and 100+ others
- Use different models for different tasks
- Compare outputs from multiple models

### 3. **Reliability**
- Automatic fallback if primary model fails
- No vendor lock-in
- Redundancy across providers

### 4. **Flexibility**
- Switch models without code changes (just environment variables)
- Test new models easily
- Optimize for your specific use case

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Provider Selection
AI_PROVIDER=openrouter  # or "anthropic" for direct Claude

# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Model Selection
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
PRESCREENING_MODEL=meta-llama/llama-3.1-8b-instruct
COVER_LETTER_MODEL=anthropic/claude-3.5-sonnet
RESUME_MODEL=openai/gpt-4-turbo
FALLBACK_MODEL=google/gemini-pro-1.5

# Cost Optimization
USE_CHEAP_PRESCREENING=true
CHEAP_MODEL_THRESHOLD=60
MAX_COST_PER_JOB=0.50

# Ensemble Analysis
ENABLE_ENSEMBLE=false
ENSEMBLE_MODELS=anthropic/claude-3.5-sonnet,openai/gpt-4-turbo,google/gemini-pro-1.5
```

### Getting an OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up for an account
3. Go to Settings → API Keys
4. Create a new API key
5. Add credits to your account (starts at $5)

## Analysis Strategies

The system supports **4 different analysis strategies**:

### 1. **Two-Tier Analysis** (Recommended for cost savings)

Uses a cheap model for prescreening, then an expensive model only for promising jobs.

```
Job → Cheap Model ($0.10/M) → Score ≥ 60? → Expensive Model ($15/M) → Final Score
                               ↓ No
                           Skip expensive analysis
```

**Cost Savings**: 70-80% for jobs that don't meet threshold

**Configuration**:
```bash
AI_PROVIDER=openrouter
USE_CHEAP_PRESCREENING=true
CHEAP_MODEL_THRESHOLD=60
PRESCREENING_MODEL=meta-llama/llama-3.1-8b-instruct
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
```

### 2. **Ensemble Analysis** (Most accurate, highest cost)

Uses multiple models and combines their scores for maximum accuracy.

```
Job → Model 1 (Score: 85)
    → Model 2 (Score: 78)  → Average: 82, Confidence: High
    → Model 3 (Score: 83)
```

**Benefits**: More robust, catches edge cases, reduces single-model bias

**Configuration**:
```bash
AI_PROVIDER=openrouter
ENABLE_ENSEMBLE=true
ENSEMBLE_MODELS=anthropic/claude-3.5-sonnet,openai/gpt-4-turbo,google/gemini-pro-1.5
```

### 3. **Single Model with Fallback** (Balanced)

Uses one primary model with automatic fallback to a backup model if primary fails.

**Configuration**:
```bash
AI_PROVIDER=openrouter
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
FALLBACK_MODEL=google/gemini-pro-1.5
```

### 4. **Direct Claude** (Original, simple)

Uses Anthropic's Claude API directly (no OpenRouter).

**Configuration**:
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Model Recommendations

### For Job Analysis

**Budget-Conscious**:
- Prescreening: `meta-llama/llama-3.1-8b-instruct` ($0.10/M tokens)
- Final: `anthropic/claude-3-haiku` ($0.25/M tokens)

**Balanced**:
- Prescreening: `google/gemini-flash-1.5` ($0.075/M tokens)
- Final: `anthropic/claude-3.5-sonnet` ($3/M tokens)

**Premium**:
- Single: `anthropic/claude-3-opus` ($15/M tokens)
- Or Ensemble: Claude + GPT-4 + Gemini

### For Cover Letters

**Best Quality**: `anthropic/claude-3.5-sonnet` or `openai/gpt-4-turbo`

**Cost-Effective**: `anthropic/claude-3-haiku` or `google/gemini-pro-1.5`

### Model Pricing (per 1M tokens)

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| meta-llama/llama-3.1-8b | $0.10 | $0.10 | Prescreening |
| google/gemini-flash-1.5 | $0.075 | $0.30 | Fast analysis |
| anthropic/claude-3-haiku | $0.25 | $1.25 | Budget analysis |
| google/gemini-pro-1.5 | $1.25 | $5.00 | Balanced |
| anthropic/claude-3.5-sonnet | $3.00 | $15.00 | Premium analysis |
| openai/gpt-4-turbo | $10.00 | $30.00 | Premium analysis |
| anthropic/claude-3-opus | $15.00 | $75.00 | Best quality |

See full pricing: https://openrouter.ai/models

## Cost Comparison Examples

### Scenario: Analyzing 50 jobs

**Original (Direct Claude Sonnet)**:
- 50 jobs × 10K tokens × $15/M = **$7.50**

**Two-Tier (Llama prescreening → Claude Sonnet)**:
- 50 jobs × 10K tokens × $0.10/M = $0.50 (prescreening)
- 15 jobs pass threshold × 10K tokens × $15/M = $2.25 (deep analysis)
- **Total: $2.75** (63% savings)

**Ensemble (3 premium models)**:
- 50 jobs × 10K tokens × ($15 + $30 + $5)/M = **$25.00**
- More accurate but 3.3x more expensive

## API Usage

### Get Statistics

```bash
curl http://localhost:8000/api/v1/stats/ai
```

Response:
```json
{
  "success": true,
  "stats": {
    "provider": "openrouter",
    "config": {
      "use_ensemble": false,
      "use_prescreening": true,
      "max_cost_per_job": 0.5
    },
    "openrouter": {
      "total_api_calls": 127,
      "total_cost": 3.45
    }
  }
}
```

### Override Analysis Strategy

```python
# In your code
from app.services.ai_service import get_ai_service

ai_service = get_ai_service()

# Force ensemble for this specific job
result = await ai_service.analyze_job_fit(
    job_description=desc,
    company=company,
    job_title=title,
    use_ensemble=True,  # Override config
    use_prescreening=False
)
```

## Best Practices

### 1. Start Cheap, Scale Up

```bash
# Week 1: Test with cheap models
PRESCREENING_MODEL=meta-llama/llama-3.1-8b-instruct
ANALYSIS_MODEL=google/gemini-flash-1.5

# Week 2: Compare with premium
ENABLE_ENSEMBLE=true
ENSEMBLE_MODELS=google/gemini-flash-1.5,anthropic/claude-3.5-sonnet

# Production: Optimize based on results
USE_CHEAP_PRESCREENING=true
CHEAP_MODEL_THRESHOLD=65
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
```

### 2. Monitor Performance

Track which models give you the best results:

```bash
# Check stats regularly
curl http://localhost:8000/api/v1/stats/ai
```

### 3. Set Cost Limits

```bash
MAX_COST_PER_JOB=0.50  # Stop if a single job exceeds $0.50
```

### 4. Use Fallbacks

Always configure a fallback model:

```bash
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet
FALLBACK_MODEL=google/gemini-pro-1.5  # Free tier friendly
```

## Troubleshooting

### "Invalid API key"
- Verify OpenRouter API key is correct
- Check you have credits in your OpenRouter account
- Ensure key has proper permissions

### "Model not found"
- Check model name format: `provider/model-name`
- Verify model is available on OpenRouter: https://openrouter.ai/models
- Some models require special access

### "Rate limited"
- OpenRouter has rate limits per model
- Switch to a different model temporarily
- Upgrade your OpenRouter plan

### Costs higher than expected
- Check if ensemble is accidentally enabled
- Verify prescreening threshold is appropriate
- Monitor stats endpoint for usage patterns

## Migration from Direct Claude

If you're currently using direct Claude API:

**Before**:
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**After** (with OpenRouter):
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxxx
ANALYSIS_MODEL=anthropic/claude-3.5-sonnet  # Same Claude model
```

No code changes needed! The system automatically routes through the new service.

## Advanced: Custom Model Routing

You can create your own routing logic by extending `AIService`:

```python
# custom_ai_service.py
from app.services.ai_service import AIService

class CustomAIService(AIService):
    async def analyze_job_fit(self, **kwargs):
        # Custom logic: use cheaper models for startups
        if "startup" in kwargs.get("company", "").lower():
            kwargs["use_prescreening"] = True
            kwargs["use_ensemble"] = False

        return await super().analyze_job_fit(**kwargs)
```

## Resources

- **OpenRouter Docs**: https://openrouter.ai/docs
- **Model Comparisons**: https://openrouter.ai/models
- **Pricing Calculator**: https://openrouter.ai/models (includes cost estimates)
- **API Status**: https://status.openrouter.ai/

## Support

For issues with OpenRouter integration:
1. Check stats endpoint: `GET /api/v1/stats/ai`
2. Review logs for error messages
3. Test with a simpler model first
4. Check OpenRouter status page

For questions about specific models, consult the OpenRouter documentation or model provider's docs.
