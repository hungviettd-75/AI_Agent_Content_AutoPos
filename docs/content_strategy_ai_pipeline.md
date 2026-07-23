# Content Strategy AI Pipeline

## Current Flow

Weekly planning currently flows from Streamlit UI to `services.content_service.create_weekly_plan()`, then to prompt templates in `agents.prompt_templates`, then to `services.gemini_client.generate_weekly_plan_json()`. The old JSON cleaner was optimized for JSON arrays and weekly fields.

The Strategy Center keeps Gemini access outside the UI. UI code should call `ContentStrategyService`, and service code owns context loading, prompt selection, retry, JSON repair, validation, and persistence.

## New Service Flow

```text
UI / future wizard
-> ContentStrategyService
-> StrategyContextService
-> agents.content_strategy_prompts
-> StrategyGenerationService
-> services.gemini_client
-> ContentStrategyJSONParser
-> ContentStrategyValidator
-> ContentStrategyGenerationRepository
-> normalized strategy tables
```

## Safety Rules

- All public service calls require `workspace_id` and `company_id`.
- Company ownership is validated before AI generation and before persistence.
- Gemini calls use bounded retry with exponential backoff for timeout, 429, and 503 style failures.
- JSON repair is attempted once after parse or schema validation failure.
- Validation runs before database writes.
- Strategy creation is atomic: if any generated child row fails, the root strategy rolls back.
- Partial regeneration replaces only the requested section and preserves unrelated strategy data.
- API keys, tokens, JWTs, and raw sensitive provider errors are redacted from logs.
- AI cost/usage is estimated and written to `ai_logs` when available.

## Output Schemas

The main root object is `content_strategy.v1`:

```json
{
  "schema_version": "content_strategy.v1",
  "task": "full_strategy",
  "strategy_summary": {
    "name": "string",
    "description": "string",
    "campaign_theme": "string"
  },
  "business_goals": [],
  "kpis": [],
  "lead_magnets": [],
  "pillars": [],
  "subtopics": [],
  "content_angles": [],
  "content_formats": [],
  "content_calendar": []
}
```

Each section is validated for required fields, type correctness, references, dates, and duplicates before persistence.

## Partial Regeneration

`ContentStrategyService.regenerate_section()` supports:

- `business_goals`
- `kpis`
- `lead_magnets`
- `pillars`
- `subtopics`
- `content_angles`
- `content_formats`
- `content_calendar`

The prompt includes the existing strategy and asks Gemini to preserve unrelated sections. Persistence still replaces only the requested section.

## Failure Contract

Generation failures return:

```json
{
  "ok": false,
  "error": {
    "code": "timeout|provider_unavailable|malformed_json|validation_failed|generation_failed",
    "message": "safe message",
    "retryable": true,
    "details": {}
  }
}
```

The service does not silently fall back to fake data.
