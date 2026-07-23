"""Prompt templates for AI Content Strategy Center."""

import json


SCHEMA_VERSION = "content_strategy.v1"
PROMPT_VERSION = "content_strategy_center.2026-07-20"


def _compact_json(value) -> str:
    return json.dumps(value or {}, ensure_ascii=False, indent=2)


def build_content_strategy_prompt(task: str, context: dict, existing_strategy: dict = None) -> str:
    """Build a JSON-only prompt for strategy generation or partial regeneration."""
    existing_block = _compact_json(existing_strategy) if existing_strategy else "{}"
    context_block = _compact_json(context)
    return f"""
You are a senior AI Content Strategist for B2B and creator-led businesses.

TASK
Generate the requested content strategy section: {task}.

INPUT CONTEXT
Use only the context below. If optional data is missing, infer conservatively from available data.
Do not invent fake analytics, fake case studies, fake customers, or fake historical performance.

{context_block}

EXISTING STRATEGY
For partial regeneration, preserve all sections that are not requested.
Never rewrite unrelated sections.

{existing_block}

OUTPUT RULES
- Return valid JSON only.
- Root must be a JSON object, not an array.
- No markdown fence, no comments, no prose before or after JSON.
- Use Vietnamese for user-facing text.
- Keep names concise and non-duplicated.
- Each item must include stable "key" fields when possible.

JSON SCHEMA
{{
  "schema_version": "{SCHEMA_VERSION}",
  "task": "{task}",
  "strategy_summary": {{
    "name": "string",
    "description": "string",
    "campaign_theme": "string"
  }},
  "business_goals": [
    {{
      "name": "string",
      "description": "string",
      "target_metric": "string",
      "target_value": 0,
      "timeframe": "string"
    }}
  ],
  "kpis": [
    {{
      "metric_name": "string",
      "target_value": 0,
      "unit": "string"
    }}
  ],
  "lead_magnets": [
    {{
      "name": "string",
      "description": "string",
      "asset_type": "checklist|template|ebook|webinar|audit|calculator|other",
      "pillar_key": "string"
    }}
  ],
  "pillars": [
    {{
      "key": "string",
      "name": "string",
      "description": "string",
      "business_goal": "string",
      "target_persona": ["string"],
      "recommended_platforms": ["facebook", "linkedin", "zalo", "instagram", "youtube", "tiktok", "blog", "email"],
      "priority": 1
    }}
  ],
  "subtopics": [
    {{
      "key": "string",
      "pillar_key": "string",
      "name": "string",
      "description": "string",
      "priority": 1
    }}
  ],
  "content_angles": [
    {{
      "key": "string",
      "pillar_key": "string",
      "subtopic_key": "string",
      "title": "string",
      "description": "string",
      "hook": "string",
      "cta": "string",
      "goal": "awareness|engagement|lead_generation|conversion|retention|education"
    }}
  ],
  "content_formats": [
    {{
      "angle_key": "string",
      "platform": "facebook|linkedin|zalo|instagram|youtube|tiktok|blog|email",
      "format_type": "post|carousel|reel|short_video|long_video|article|newsletter|livestream|story",
      "name": "string",
      "description": "string",
      "specs": {{"length": "string", "cadence": "string"}}
    }}
  ],
  "content_calendar": [
    {{
      "planned_date": "YYYY-MM-DD",
      "platform": "facebook|linkedin|zalo|instagram|youtube|tiktok|blog|email",
      "title": "string",
      "brief": "string",
      "pillar_key": "string",
      "subtopic_key": "string",
      "angle_key": "string",
      "content_type": "string",
      "cta": "string"
    }}
  ]
}}
""".strip()


def build_json_repair_prompt(raw_text: str, validation_errors: list, task: str) -> str:
    errors = _compact_json(validation_errors)
    return f"""
You are a strict JSON repair system.

Repair the AI output for task "{task}" so it becomes valid JSON matching schema {SCHEMA_VERSION}.

Rules:
- Return JSON object only.
- No markdown fence.
- Preserve valid content when possible.
- Fix missing required fields with concise values derived from nearby context.
- Fix wrong types.
- Remove duplicates.
- Do not add fake analytics or fake historical data.

Validation errors:
{errors}

Raw output:
{raw_text}
""".strip()


def build_persona_generation_prompt(context: dict, count: int = 1) -> str:
    """Build a JSON-only prompt for AI-generated persona drafts."""
    context_block = _compact_json(context)
    return f"""
You are a senior audience strategist.

TASK
Generate {count} audience persona draft(s) for the content strategy.

INPUT CONTEXT
Use only the context below. Do not invent fake customers, private personal data,
fake research, fake analytics, or sensitive demographic details. If a field is
uncertain, keep it broad and business-relevant.

{context_block}

OUTPUT RULES
- Return valid JSON only.
- Root must be a JSON object with a "personas" array.
- No markdown fence, no comments, no prose before or after JSON.
- Use Vietnamese for user-facing text.
- Every persona must be marked as an AI-generated draft.

JSON SCHEMA
{{
  "personas": [
    {{
      "name": "string",
      "role": "string",
      "industry": "string",
      "company_size": "string",
      "demographics": "string",
      "goals": ["string"],
      "pain_points": ["string"],
      "fears": ["string"],
      "desires": ["string"],
      "objections": ["string"],
      "buying_triggers": ["string"],
      "decision_authority": "string",
      "preferred_channels": ["string"],
      "preferred_content_formats": ["string"],
      "content_depth_preference": "string",
      "language_style": "string",
      "customer_journey_stage": "string",
      "ai_generated_draft": true
    }}
  ]
}}
""".strip()

def build_pillar_generation_prompt(context: dict, count: int = 10, regenerate_index: int = None) -> str:
    """Build a JSON-only prompt for AI-generated content pillar drafts."""
    context_block = _compact_json(context)
    regenerate_note = (
        f"Regenerate only pillar index {regenerate_index}. Preserve unchanged manual edits in existing_pillars."
        if regenerate_index is not None
        else "Generate the recommended set of pillars. Use requested_pillar_count as guidance, not a hard requirement."
    )
    return f"""
You are a senior content strategy architect.

TASK
Generate content pillar draft(s) for Step 5: Content Pillars.
{regenerate_note}

INPUT CONTEXT
Use all available context below:
- Business Context
- Brand Identity
- Audience Personas
- Business Goals
- Existing Knowledge
- Existing Pillars when regenerating part of the plan

Do not invent fake analytics, fake customers, fake case studies, or private data.
If the strategy does not need exactly {count} pillars, return the number that is strategically appropriate.

{context_block}

OUTPUT RULES
- Return valid JSON only.
- Root must be a JSON object with a "pillars" array.
- No markdown fence, no comments, no prose before or after JSON.
- Use Vietnamese for user-facing text.
- Pillar names must be concise and intentionally distinct.
- The sum of content_ratio across the final suggested set should be 100 when returning a full set.

JSON SCHEMA
{{
  "pillars": [
    {{
      "name": "string",
      "description": "string",
      "strategic_purpose": "string",
      "business_goals": ["string"],
      "target_personas": ["string"],
      "recommended_channels": ["facebook", "linkedin", "zalo", "instagram", "youtube", "tiktok", "blog", "email"],
      "content_ratio": 10,
      "priority": "high|medium|low",
      "differentiation_angle": "string",
      "do_guidance": ["string"],
      "dont_guidance": ["string"],
      "status": "active"
    }}
  ]
}}
""".strip()



def build_subtopic_generation_prompt(context: dict, subtopics_per_pillar: int = 3, batch: dict = None) -> str:
    """Build a JSON-only prompt for Step 6 subtopic batch generation."""
    context_block = _compact_json(context)
    batch_block = _compact_json(batch or {})
    return f"""
You are a senior content strategist.

TASK
Generate Step 6 Subtopics for the selected content pillars only.

INPUT CONTEXT
{context_block}

BATCH REQUEST
{batch_block}

RULES
- Return valid JSON only.
- Root must be a JSON object with a "subtopics" array.
- Use Vietnamese for user-facing text.
- Generate up to {subtopics_per_pillar} subtopics per selected pillar.
- Do not duplicate existing_subtopics by name, intent, or semantic meaning.
- Do not overwrite or reinterpret manual items.
- Do not invent fake analytics, customers, or case studies.

JSON SCHEMA
{{
  "subtopics": [
    {{
      "pillar_id": "string",
      "name": "string",
      "description": "string",
      "target_persona": "string",
      "business_goal": "string",
      "intent": "search|audience intent string",
      "funnel_stage": "awareness|consideration|decision|retention",
      "priority": "high|medium|low",
      "trend_classification": "evergreen|trending|hybrid",
      "suggested_channels": ["facebook", "linkedin", "zalo", "instagram", "youtube", "tiktok", "blog", "email"],
      "status": "draft"
    }}
  ]
}}
""".strip()


def build_angle_generation_prompt(context: dict, angles_per_subtopic: int = 5, batch: dict = None) -> str:
    """Build a JSON-only prompt for Step 7 content angle batch generation."""
    context_block = _compact_json(context)
    batch_block = _compact_json(batch or {})
    return f"""
You are a senior editorial strategist.

TASK
Generate Step 7 Content Angles for the selected subtopics only.

INPUT CONTEXT
{context_block}

BATCH REQUEST
{batch_block}

RULES
- Return valid JSON only.
- Root must be a JSON object with a "content_angles" array.
- Use Vietnamese for user-facing text.
- Generate up to {angles_per_subtopic} angles per selected subtopic.
- Use a diverse category mix from allowed_categories.
- Do not duplicate existing_angles by title, hook, core insight, or semantic meaning.
- Do not overwrite or reinterpret manual items.
- Do not invent fake analytics, customers, or case studies.

JSON SCHEMA
{{
  "content_angles": [
    {{
      "subtopic_id": "string",
      "category": "How-to|Mistakes|Checklist|Case Study|Comparison|Myth vs Fact|Framework|Step-by-step|ROI|Cost|Risk|Contrarian Opinion|Trend|Prediction|Behind the Scenes|Demonstration|FAQ|Before/After|Storytelling|Debate|Template|Prompt|Tool List|Executive Insight",
      "working_title": "string",
      "hook_idea": "string",
      "core_insight": "string",
      "intended_emotion": "string",
      "target_persona": "string",
      "funnel_stage": "awareness|consideration|decision|retention",
      "cta_type": "soft|lead_magnet|demo|consultation|purchase|subscribe|community",
      "evidence_requirement": "string",
      "trend_classification": "evergreen|trending|hybrid",
      "priority": "high|medium|low",
      "risk_level": "low|medium|high",
      "status": "draft"
    }}
  ]
}}
""".strip()
