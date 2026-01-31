# Unified Model Evaluation Notebook - Usage Guide

## Overview

The enhanced notebook now supports **30 models** across 5 providers:
- **OpenAI** (7 models) - Direct API
- **Claude/Anthropic** (2 models) - Direct API
- **Gemini/Google** (2 models) - Direct API
- **OpenRouter** (8 models) - Unified routing
- **xAI** (1 model via OpenRouter) - Grok models

## New Models Added from openrouter_testing_v2.py

The following OpenRouter models are now available:

### 1. **openai/gpt-5.2**
- Context: 128K tokens
- Cost: $1.75/M input, $14/M output
- Vision: ✅ Yes

### 2. **google/gemini-3-pro-preview**
- Context: 1M tokens
- Cost: $2.0/M input, $12.0/M output
- Vision: ✅ Yes

### 3. **anthropic/claude-opus-4.5**
- Context: 200K tokens
- Cost: $5.0/M input, $25.0/M output
- Vision: ✅ Yes

### 4. **deepseek/deepseek-v3.2**
- Context: 64K tokens
- Cost: $0.25/M input, $0.38/M output
- Vision: ❌ No

### 5. **z-ai/glm-4.7**
- Context: 128K tokens
- Cost: $0.40/M input, $1.50/M output
- Vision: ✅ Yes

### 6. **xiaomi/mimo-v2-flash:free**
- Context: 32K tokens
- Cost: **FREE!**
- Vision: ❌ No

### 7. **x-ai/grok-4.1-fast**
- Context: 2M tokens
- Cost: $0.20/M input, $0.50/M output
- Vision: ✅ Yes

### 8. **deepseek/deepseek-r1-0528:free**
- Context: 163,840 tokens
- Cost: **FREE!**
- Vision: ❌ No
- Note: Uses OpenRouter auto-routing (provider forcing disabled)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install openai anthropic google-generativeai tiktoken transformers pandas openpyxl pyxlsb python-dotenv tqdm pillow
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```env
# OpenAI Direct API (optional if using OpenRouter)
OPENAI_API_KEY=your_openai_key

# Anthropic Direct API (optional if using OpenRouter)
ANTHROPIC_API_KEY=your_anthropic_key

# Google Direct API (optional if using OpenRouter)
GOOGLE_API_KEY=your_google_key

# OpenRouter (RECOMMENDED - use one API for all models)
OPENROUTER_API_KEY=your_openrouter_key
USE_OPENROUTER=true  # Set to true to route ALL models through OpenRouter
```

### 🎯 Recommended Setup: Use OpenRouter for Everything

Set `USE_OPENROUTER=true` to route all models through OpenRouter's unified API:

**Advantages:**
- ✅ **Single API key** - No need for separate OpenAI/Anthropic/Google keys
- ✅ **Provider forcing** - Prevents fallback to alternative providers (`allow_fallbacks: false`)
- ✅ **Seed support** - Reproducible results with `seed=42`
- ✅ **Consistent interface** - Same API format for all models
- ✅ **Better error handling** - Unified error responses

## Usage Examples

### Example 1: Use OpenAI Direct API

```python
MODEL = "gpt-4o-2024-11-20"
DATA_PATH = "./data_subset_olive/"
TOKENS_FOR_GENERATION = 6000
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0
```

### Example 2: Use OpenRouter Model

```python
# Make sure .env has:
# USE_OPENROUTER=true
# OPENROUTER_API_KEY=your_key

MODEL = "google/gemini-3-pro-preview"  # or any OpenRouter model
DATA_PATH = "./data_subset_olive/"
TOKENS_FOR_GENERATION = 6000
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0
```

### Example 3: Use Free Model (Xiaomi)

```python
MODEL = "xiaomi/mimo-v2-flash:free"  # Completely free!
DATA_PATH = "./data_subset_olive/"
TOKENS_FOR_GENERATION = 6000
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0
```

### Example 4: Use Cost-Effective Model (Deepseek)

```python
MODEL = "deepseek/deepseek-v3.2"  # Very cheap
DATA_PATH = "./data_subset_olive/"
TOKENS_FOR_GENERATION = 6000
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0
```

## Key Features

### ✅ Unified Interface
- Same code works for all 26 models
- Automatic provider detection
- Consistent error handling

### ✅ Smart Tokenization
- **OpenAI models**: Uses `tiktoken` for accurate counting
- **Claude models**: Uses `transformers` with Claude tokenizer
- **Gemini/Other models**: Uses GPT2 tokenizer approximation
- **OpenRouter models**: Automatically selects appropriate tokenizer based on model type

### ✅ Robust Error Handling
- Automatic retry with exponential backoff
- Rate limit handling
- Progress saving (resume from where you left off)
- Error logging

### ✅ Cost Tracking
- Accurate cost calculation per model
- Real-time cost updates
- Total cost reporting

### ✅ Vision Support Detection
- Automatically handles image inputs for vision-capable models
- Gracefully skips images for text-only models

### ✅ NEW: Provider Forcing (OpenRouter)
- **Forces specific provider** - No fallback to alternative providers
- Set `allow_fallbacks: false` automatically for OpenRouter models
- Ensures you get exactly the model you requested
- Example: `openai/gpt-5.2` will ONLY use OpenAI, never fallback to another provider

### ✅ NEW: Seed Support for Reproducibility
- **Deterministic results** with `seed=42` (default)
- Essential for `temperature=0` evaluations
- Same input → Same output (reproducible experiments)
- Works with OpenAI and OpenRouter

### ✅ NEW: Folder Management & Auto-Resume
- **Smart folder detection** - Finds existing evaluation runs automatically
- **Auto-resume capability** - Continue from where you left off
- **Hierarchical structure** - `./save_process/<model_name>/<timestamp>/`
- **Error cleanup** - Option to remove error entries before resuming
- **Run statistics** - Shows samples, questions, errors, and timestamps for each run

### ✅ NEW: Intelligent Resume (v2.3)
- **Question-level tracking** - Tracks which specific questions are completed, not just line counts
- **Smart error handling** - Ignores error entries, only re-runs failed/missing questions
- **Precise re-runs** - Re-runs only the exact questions that failed, regardless of position
- **Clear feedback** - Shows: `"Resuming sample - 12/13 questions already successful"`

### ✅ NEW: Dual Cost Tracking (v2.3)
- **Run cost** - Shows cost for new questions processed in current run
- **Timestamp cost** - Shows cumulative cost across all runs for this timestamp
- **Always visible** - Displays total cost even when re-running completed timestamps
- **Example output**:
  ```
  💰 Cost for this run (new questions only): $0.086968
  💰 Total cost for timestamp (all runs): $1.220000
  ```

### ✅ NEW: Smart Retry Logic (v2.3)
- **Expanded error detection** - Retries rate limits, timeouts, network errors, server errors
- **Exponential backoff** - 5s → 10s → 20s → 40s → 80s between retries
- **Error categorization** - Shows specific error type (Rate limit, Timeout, Network, Server)
- **Fast failure** - Non-retriable errors (like malformed responses) fail immediately

## Model Selection Guide

### For Best Quality
1. **gpt-4o-2024-11-20** - Best balance, stable, supports seed
2. **claude-3-5-sonnet-20240620** - High quality, stable
3. **gemini-1.5-pro-exp-0801** - Large context, experimental but stable

### ⚠️ Preview Models (Not Recommended for Benchmarks)
- **google/gemini-3-pro-preview** - Preview, non-deterministic
- **openai/gpt-5.2** - Preview, may change behavior
- **anthropic/claude-opus-4.5** - Preview, expensive
- These are great for exploration but NOT for reproducible benchmarks

### For Cost Efficiency
1. **xiaomi/mimo-v2-flash:free** - Free!
2. **deepseek/deepseek-r1-0528:free** - Free!
3. **x-ai/grok-4.1-fast** - Very cheap ($0.20-$0.50/M)
4. **deepseek/deepseek-v3.2** - Very cheap ($0.25-$0.38/M)
5. **z-ai/glm-4.7** - Affordable ($0.40-$1.50/M)

### For Large Context
1. **x-ai/grok-4.1-fast** - 2M tokens
2. **google/gemini-3-pro-preview** - 1M tokens
3. **gemini-1.5-flash** - 1M tokens
4. **gemini-1.5-pro-exp-0801** - 1M tokens

### For Vision Tasks
- All models support vision except:
  - ❌ deepseek/deepseek-v3.2
  - ❌ deepseek/deepseek-r1-0528:free
  - ❌ xiaomi/mimo-v2-flash:free
  - ❌ gpt-3.5-turbo-0125

### For Reproducible Benchmarks (v2.3)
Models ranked by determinism with `temperature=0` and `seed=42`:

| Model | Deterministic? | Notes |
|-------|---------------|-------|
| **gpt-4o-2024-11-20** | ✅✅✅ Excellent | Official seed support, most reliable |
| **gpt-4o-2024-05-13** | ✅✅✅ Excellent | Official seed support |
| **gpt-4-turbo-2024-04-09** | ✅✅ Good | Seed support, stable |
| **claude-3-5-sonnet-20240620** | ✅✅ Good | Stable, mostly consistent |
| **gemini-1.5-flash** | ✅ Fair | Stable but no seed support |
| **gemini-1.5-pro-exp-0801** | ✅ Fair | Experimental but consistent |
| **google/gemini-3-pro-preview** | ❌ Poor | Preview model, non-deterministic |
| **openai/gpt-5.2** | ❌ Poor | Preview model, behavior may change |
| **deepseek models** | ⚠️ Variable | Cheap but results vary |

**Recommendation for benchmarks**: Use `gpt-4o-2024-11-20` or `claude-3-5-sonnet-20240620` with `temperature=0` and `seed=42`.

## How OpenRouter Works

OpenRouter provides a unified API for accessing multiple AI models:

1. **Single API Key**: Use one key for all models
2. **Automatic Routing**: Routes to appropriate provider
3. **Consistent Interface**: Same API format for all models
4. **Cost Optimization**: Competitive pricing across providers

### OpenRouter vs Direct API

| Aspect | OpenRouter | Direct API |
|--------|-----------|------------|
| Setup | Single API key | Multiple API keys needed |
| Cost | Slightly marked up | Direct provider pricing |
| Models | 100+ models | Provider-specific only |
| Interface | Unified | Provider-specific |
| Best For | Experimenting, flexibility | Production, lowest cost |

## Troubleshooting

### "OpenRouter client not initialized"
**Solution**: Set in `.env`:
```env
USE_OPENROUTER=true
OPENROUTER_API_KEY=your_key
```

### "Unknown model: model_name"
**Solution**: Check `MODEL_CONFIGS` in the notebook. Model name must match exactly.

### Tokenizer Warnings
**Solution**: Install missing dependencies:
```bash
pip install tiktoken transformers
```

### Rate Limit Errors
**Solution**: The notebook automatically retries with backoff. If persistent:
1. Reduce request rate
2. Switch to a different model
3. Check your API quota

## Cost Comparison

Sample calculation for 100K input tokens + 5K output tokens:

| Model | Input Cost | Output Cost | Total |
|-------|-----------|-------------|--------|
| xiaomi/mimo-v2-flash:free | $0.00 | $0.00 | **$0.00** |
| deepseek/deepseek-r1-0528:free | $0.00 | $0.00 | **$0.00** |
| deepseek/deepseek-v3.2 | $0.025 | $0.019 | **$0.044** |
| z-ai/glm-4.7 | $0.040 | $0.075 | **$0.115** |
| x-ai/grok-4.1-fast | $0.020 | $0.025 | **$0.045** |
| openai/gpt-5.2 | $0.175 | $0.700 | **$0.875** |
| google/gemini-3-pro-preview | $0.200 | $0.600 | **$0.800** |
| anthropic/claude-opus-4.5 | $0.500 | $1.250 | **$1.750** |

## Advanced Usage

### Using Different Temperatures
```python
# For deterministic results
TEMPERATURE = 0

# For creative outputs
TEMPERATURE = 0.7

# For maximum creativity
TEMPERATURE = 1.0
```

### Custom Token Limits
```python
# Reserve more tokens for generation
TOKENS_FOR_GENERATION = 10000

# Allow longer outputs
MAX_OUTPUT_TOKENS = 8192
```

### Resume Failed Runs (Enhanced in v2.3)
The notebook has intelligent folder management and resume logic:
1. **Automatic detection** - Finds existing runs for the model
2. **Interactive selection** - Choose to resume or create new run
3. **Auto-resume mode** - Set `AUTO_RESUME = True` to automatically continue from most recent run
4. **Error cleanup** - Option to remove error entries before resuming
5. **Question-level tracking** - Tracks exactly which questions are completed (v2.3)
6. **Precise re-runs** - Only processes failed/missing questions (v2.3)

**Example output:**
```
Resuming 00000001 - 12/13 questions already successful
Will process 1 remaining/errored questions
💰 Existing costs from completed questions: $1.134032

Processing sample 00000001...
  Question 1/13: ✓ Already completed
  Question 2/13: ✓ Already completed
  Question 3/13: ✓ Already completed
  Question 4/13: In: 35,234 tok | Out: 1,456 tok | Cost: $0.086968 | Total: $1.220000
  Question 5/13: ✓ Already completed
  ...

================================================================================
🎉 Evaluation complete!
Questions processed (new): 1
💰 Cost for this run (new questions only): $0.086968
💰 Total cost for timestamp (all runs): $1.220000
================================================================================
```

**Folder Structure:**
```
./save_process/
├── model_name/
│   ├── 20260126_120000/  # Run 1
│   │   ├── sample1.json
│   │   ├── results.json
│   │   └── evaluation_summary.txt
│   └── 20260127_150000/  # Run 2
│       ├── sample1.json
│       └── results.json
```

## Evaluation Pipeline Scripts

### compute_answer.py
Evaluates model predictions by comparing them against ground truth answers.

**Features:**
- Uses GPT-4o to judge if predictions match ground truth
- **NEW**: Safety check for missing predictions (treats as incorrect)
- Handles error entries gracefully
- Saves results to `results.json` and `results_process.json`

**Usage:**
```python
MODEL = "deepseek/deepseek-r1-0528:free"
TIMESTAMP = "20260127_030449"
DATA_JSON_PATH = "./data_sample.json"
```

### show_result.py
Displays evaluation results with comprehensive metrics and saves summary to file.

**Features:**
- **NEW**: Saves formatted summary to `evaluation_summary.txt`
- Calculates task-level and competition-level accuracy
- Shows per-challenge breakdown
- Tracks inference time and costs

**Output Format:**
```
Model Used: deepseek/deepseek-r1-0528:free
Timestamp: 20260127_030449
Total Questions: 13
Total Challenges: 1
Total Inference Time: 45.23 seconds
Total Cost: $ 0.00
Task Level Accuracy: 84.62 %
Competition Level Accuracy: 84.62 %
```

## Best Practices

1. **Start with free/cheap models** for testing (DeepSeek R1, Xiaomi)
2. **Use vision models only when needed** (they cost more)
3. **Monitor costs** in real-time during evaluation
4. **Save API keys securely** in `.env` (never commit to git)
5. **Test with small datasets** before full evaluation
6. **Use appropriate temperature** (0 for analysis, higher for creativity)
7. **Enable auto-resume** for long-running evaluations
8. **Review evaluation_summary.txt** for quick metrics overview
9. **NEW (v2.3)**: Don't manually delete error entries - the notebook handles resume automatically
10. **NEW (v2.3)**: Check "Total cost for timestamp" to see true cumulative costs
11. **NEW (v2.3)**: Use stable models (not preview) for reproducible benchmarks:
    - ✅ Best: `gpt-4o-2024-11-20` (most deterministic with seed)
    - ✅ Good: `gemini-1.5-flash` (cheap, mostly stable)
    - ❌ Avoid: `google/gemini-3-pro-preview` (preview models are non-deterministic)

## Support

For issues or questions:
1. Check the notebook cell outputs for error messages
2. Verify `.env` configuration
3. Check API key validity
4. Review model availability on provider websites

## Known Issues & Solutions

### DeepSeek Provider Forcing
**Issue**: DeepSeek models return 404 errors when provider forcing is enabled.

**Solution**: Provider forcing is automatically disabled for DeepSeek models. OpenRouter uses auto-routing instead. You'll see:
```
🔓 Provider forcing disabled (using OpenRouter auto-routing)
```

### Missing Predictions
**Issue**: If evaluation was interrupted and JSON has fewer predictions than questions.

**Solution**: `compute_answer.py` now automatically detects this and treats missing predictions as incorrect. You'll see a warning:
```
⚠️  Warning: Sample 00000001 has 13 questions but only 10 predictions
   Treating 3 missing predictions as incorrect
```

### Question Re-run After Error (v2.3)
**Issue**: After cleaning errors and re-running, the wrong question gets processed.

**Solution (FIXED in v2.3)**: The notebook now tracks question indices instead of line counts. Example:
```
Initial run:
- Questions 1-3: Success ✓
- Question 4: Error ❌
- Questions 5-13: Success ✓

Re-run behavior:
OLD (v2.2): Would resume from question 13 or skip entirely
NEW (v2.3): Will process ONLY question 4 (the one that failed)
```

### Cost Showing $0.00 on Re-run (v2.3)
**Issue**: When re-running a completed timestamp, cost shows $0.00 instead of actual total.

**Solution (FIXED in v2.3)**: The notebook now tracks two costs:
```
💰 Cost for this run (new questions only): $0.000000
💰 Total cost for timestamp (all runs): $1.220000  ← Real total!
```

### Duplicate Costs in show_result.py (v2.3)
**Issue**: If sample has error + retry for same question, costs were counted twice.

**Solution (FIXED in v2.3)**: `show_result.py` now deduplicates by question_idx, keeping only the latest successful entry.

---

**Last Updated**: 2026-01-28
**Notebook Version**: 2.3 (Intelligent Resume + Cost Tracking)
