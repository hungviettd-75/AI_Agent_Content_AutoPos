FRAMEWORK_SECTIONS = [
    "ROLE",
    "TASK",
    "CONTEXT",
    "DATA",
    "OUTPUT",
    "CONSTRAINTS",
]

TOOL_EXAMPLES = {
    "ChatGPT": {
        "ROLE": "You are a senior AI productivity coach who helps non-technical teams use ChatGPT safely and effectively.",
        "TASK": "Create a step-by-step guide for turning messy meeting notes into clear action items.",
        "CONTEXT": "The audience is office staff who use ChatGPT for daily work but often get vague or generic answers.",
        "DATA": "Raw meeting notes, attendee names, decisions made, deadlines, blockers, and open questions.",
        "OUTPUT": "A table with Owner, Task, Deadline, Priority, Risk, and Follow-up Question.",
        "CONSTRAINTS": "Do not invent decisions. Mark missing information as 'Need clarification'. Use simple Vietnamese.",
    },
    "Claude": {
        "ROLE": "You are a careful reasoning assistant specialized in long document analysis.",
        "TASK": "Analyze a policy document and extract the practical implications for each department.",
        "CONTEXT": "The company needs a neutral, non-sales summary that managers can use for internal planning.",
        "DATA": "Policy text, department list, current workflow notes, compliance concerns, and key deadlines.",
        "OUTPUT": "A markdown brief with Summary, Department Impact, Risks, Recommended Actions, and Questions.",
        "CONSTRAINTS": "Separate facts from assumptions. Quote only short relevant phrases. Avoid legal advice.",
    },
    "Gemini": {
        "ROLE": "You are a multimodal AI trainer who explains concepts with practical examples.",
        "TASK": "Create a beginner-friendly tutorial for using Gemini to research and summarize a market trend.",
        "CONTEXT": "The reader is new to AI tools and needs a repeatable workflow, not theory.",
        "DATA": "Trend name, target industry, source links or pasted notes, target audience, and desired length.",
        "OUTPUT": "A tutorial with workflow steps, example prompt, expected output, and quality checklist.",
        "CONSTRAINTS": "Keep the language simple. Include examples. Do not make unsupported market claims.",
    },
    "Cursor": {
        "ROLE": "You are a senior software engineer pairing with a developer inside Cursor.",
        "TASK": "Refactor a Streamlit form without changing existing behavior.",
        "CONTEXT": "The project is a small Python app. The user wants cleaner structure and safer future edits.",
        "DATA": "Relevant file path, current function, desired fields, constraints, and any known bugs.",
        "OUTPUT": "A concise implementation plan, changed code, and a short verification checklist.",
        "CONSTRAINTS": "Keep edits scoped. Preserve current UI labels unless asked. Do not rewrite unrelated code.",
    },
    "Codex": {
        "ROLE": "You are Codex, a careful coding agent working directly in the user's local workspace.",
        "TASK": "Add a reusable module and wire it into the existing application only where needed.",
        "CONTEXT": "The user values stable behavior, readable code, and practical verification.",
        "DATA": "Workspace structure, target files, requested inputs and outputs, existing coding style, and test commands.",
        "OUTPUT": "Implemented files, a summary of changes, and verification results.",
        "CONSTRAINTS": "Do not overwrite unrelated work. Ask for permission before privileged writes. Keep changes minimal.",
    },
    "n8n": {
        "ROLE": "You are an automation architect designing practical n8n workflows.",
        "TASK": "Design an n8n workflow that turns form submissions into reviewed content drafts.",
        "CONTEXT": "A small team wants automation but still needs human approval before publishing.",
        "DATA": "Form fields, trigger source, AI tool, approval channel, destination app, and error-handling needs.",
        "OUTPUT": "A workflow blueprint with nodes, data mapping, prompt template, approval step, and failure path.",
        "CONSTRAINTS": "Do not auto-publish without approval. Include retry/error handling. Avoid storing secrets in plain text.",
    },
}

def build_prompt_framework(role, task, context, data, output, constraints):
    values = {
        "ROLE": role,
        "TASK": task,
        "CONTEXT": context,
        "DATA": data,
        "OUTPUT": output,
        "CONSTRAINTS": constraints,
    }
    lines = ["## Prompt Framework", ""]
    for section in FRAMEWORK_SECTIONS:
        lines.extend([f"### {section}", str(values[section]).strip(), ""])
    return "\n".join(lines).strip()

def generate_tool_prompt_framework(tool_name):
    example = TOOL_EXAMPLES.get(tool_name)
    if not example:
        supported = ", ".join(TOOL_EXAMPLES)
        raise ValueError(f"Unsupported tool_name: {tool_name}. Supported tools: {supported}")

    return build_prompt_framework(
        role=example["ROLE"],
        task=example["TASK"],
        context=example["CONTEXT"],
        data=example["DATA"],
        output=example["OUTPUT"],
        constraints=example["CONSTRAINTS"],
    )

def generate_all_prompt_framework_examples():
    blocks = [
        "# Prompt Framework Engine",
        "",
        "Reusable structure: `ROLE -> TASK -> CONTEXT -> DATA -> OUTPUT -> CONSTRAINTS`.",
    ]

    for tool_name in TOOL_EXAMPLES:
        blocks.extend([
            "",
            f"---\n\n## {tool_name}",
            generate_tool_prompt_framework(tool_name),
        ])

    return "\n".join(blocks).strip()
