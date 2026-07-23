from config.config import TOOLS, CRITERIA, COMPARISON_DATA

def _markdown_escape(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")

def generate_comparison_table(tools=None, criteria=None):
    selected_tools = tools or TOOLS
    selected_criteria = criteria or CRITERIA

    unknown_tools = [tool for tool in selected_tools if tool not in COMPARISON_DATA]
    if unknown_tools:
        supported = ", ".join(TOOLS)
        raise ValueError(f"Unsupported tools: {', '.join(unknown_tools)}. Supported tools: {supported}")

    unknown_criteria = [item for item in selected_criteria if item not in CRITERIA]
    if unknown_criteria:
        supported = ", ".join(CRITERIA)
        raise ValueError(f"Unsupported criteria: {', '.join(unknown_criteria)}. Supported criteria: {supported}")

    headers = ["AI Tool", *selected_criteria]
    separator = ["---", *["---" for _ in selected_criteria]]
    rows = [headers, separator]

    for tool in selected_tools:
        row = [tool]
        row.extend(COMPARISON_DATA[tool][criterion] for criterion in selected_criteria)
        rows.append(row)

    return "\n".join(
        "| " + " | ".join(_markdown_escape(cell) for cell in row) + " |"
        for row in rows
    )

def generate_full_comparison_markdown():
    return "\n\n".join([
        "# AI Tool Comparison",
        "Các đánh giá dưới đây mang tính thực chiến, dùng để chọn công cụ theo nhu cầu công việc.",
        generate_comparison_table(),
    ])
