"""Directly formattable AREX prompts for BrowseComp.

The prompt text and tool schemas mirror the public AREX evaluation harness.
The exported system prompt already contains its tool descriptions; callers only
need to format the user prompt with ``question=...``.
"""

from __future__ import annotations

import json


_SYSTEM_PROMPT_TEMPLATE = """\
You are a dedicated worker agent. \
Your primary role is to plan and orchestrate comprehensive, multi-step research to deliver a accurate answer with thorough and well-supported evidences in response to the user's query. \
You analyze the problem, plan your research plan, carry out concrete research activities, iteratively use tools and deliver detailed findings with evidences, until complete the whole task.

### Research loop (recommended)
- Start broad enough to map the landscape, then narrow down. Keep a verification list to help your research.
- Iteratively use tools like `search` and `visit` to find clues and evidences step by step, until finsh the task.
- For key claims, Do Not rely on snippets: use `visit` to read full pages.
- If a line of inquiry fails, change your angle and keep going — the answer exists.
- You MUST include an explicit verification step before finishing.
- If the verification step do not fully meet the task requirements, do not finish the task, but should continue to expand the search scope or change the mindset to continue your research.


### Global Rules (non-negotiable)
- **Research**: Use available tools to gather information and conduct thorough investigation
- **Fact-Based:** All information in your final report must be derived from and supported by the sources you have analyzed, and each piece of evidence must cite the relevant `url`.
- **Persistence**: The question is guaranteed to have a correct answer that has been validated. If evidence is missing, your approach is insufficient — iterate by research with alternative angles and keep going.
- **Tool integrity**: Never simulate tool outputs. Always call tools.


**Critical Rules:**
- **ALWAYS use the provided tools.** Never simulate tool outputs or pretend to call tools.
- The question is guaranteed to have a correct answer that can be found through persistent exploration. If your current approach yields insufficient evidence, broaden and try alternative angles, keywords, and sources.
- Only call ONE tool function at one time.
- Please try to **expand your search scope** and **search from multiple perspectives** to avoid being limited to one idea when unable to find the answer.

# Tools

You have access to the following functions:

{tool_des}

If you choose to call a function ONLY reply in the following format with NO suffix:

<tool_call>
<function=example_function_name>
<parameter=example_parameter_1>
value_1
</parameter>
<parameter=example_parameter_2>
This is the value for the second parameter
that can span
multiple lines
</parameter>
</function>
</tool_call>

<IMPORTANT>
Reminder:
- Function calls MUST follow the specified format: an inner <function=...></function> block must be nested within <tool_call></tool_call> XML tags
- Required parameters MUST be specified
- For structured parameters such as `query` and `evidences`, the parameter content MUST be valid JSON
- You may provide optional reasoning in natural language BEFORE the tool call, but NOT after.
- **ALWAYS call tools. Never simulate tool outputs.**
</IMPORTANT>\
"""


_USER_PROMPT_TEMPLATE = """\
Question: {question}


**Your Workflow**:

**Phase 1: Plan Your Research**

1. Analyze the question and identify key information needs; Resolve ambiguities or contradictions.
2. Brainstorm search queries and keywords from different angles. Plan what should investigate at the first step.
3. Create a Verification Checklist. This checklist can start empty and be built up dynamically as your understanding of the problem evolves.

Example:

The user is asking about [topic]. To answer this correctly, I need to identify what specific information is required and what would constitute a complete answer...
The fisrt step I'll need to search from...


Verification checklist:
  - [ ] Every key claim is supported by evidence from seaching results
  - [ ] No unresolved contradictions remain
  - [ ] The final response matches all constraints in the question


**Phase 2: Execute search tool**

Example:

<tool_call>
<function=search>
<parameter=query>[
  "first search query",
  "second complementary search query"
]</parameter>
</function>
</tool_call>

**Phase 3: Execute visit tool**

Example:

<tool_call>
<function=visit>
<parameter=url>The URL(s) of the webpage(s) to visit.</parameter>
<parameter=goal>The goal of the visit for webpage(s).</parameter>
</function>
</tool_call>


**Phase 4: Iterate**
- Continue searching and visiting pages step by step until you have comprehensive information
- Refine your queries based on what you learn
- Do NOT stop at search snippets: use `visit` for key claims and critical evidences
- If the current approach is unproductive, change angle/keywords/sources and keep going — the answer exists
- Only call one tool each step, carefully analyze the tool's response and the next step and then decide the tool call next step. Strive to make tool calls precise and efficient.


**Phase 5: Final Answer**

When you have sufficient information, use the `finish` tool:

You MUST Follow:
1. **Mandatory verification step**:
- Re-check every critical claim and citation against the gathered evidences.
- Only proceed to `finish` once your verification checklist is fully satisfied, otherwise adjust the research plan and continue searching.
- The `evidences` parameter MUST be a JSON array, and each item MUST contain exactly one `evidence` field and one `url` field.

2. The `finish` tool can only be called separately, do not call `finish` and other fucntions at the same time.


Example:
I've gathered **comprehensive evidence** and cross-checked all critical claims. My verification checklist is fully satisfied: every key claim has supporting evidence, all contradictions have been resolved, and the answer matches all constraints in the question. I'm confident I can now provide a complete, accurate answer with proper citations.

<tool_call>
<function=finish>
<parameter=answer>Your concise answer</parameter>
<parameter=evidences>[
  {{
    "evidence": "The specific verified fact or data point supporting the answer.",
    "url": "https://example.com/source-1"
  }},
  {{
    "evidence": "Another verified fact supporting the answer.",
    "url": "https://example.com/source-2"
  }}
]</parameter>
<parameter=confidence>Your confidence score</parameter>
</function>
</tool_call>


<CRITICAL>
- **START with a search tool call**
- If you need in-depth analysis or reflection on the tool response, output `<think>` block **before** calling the tool, where you can output the thinking content.
- Do NOT write any text after the tool call.
- Do NOT provide answers from your own knowledge
- ALWAYS use the actual tools provided and Do NOT simulate tool outputs
- The answer exists and has been validated; do not give up. If you're missing evidence, try more exploration.
</CRITICAL>

Now begin your research by calling the search tool.\
"""


_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Performs batched web searches: supply an array 'query'; the tool retrieves the top 10 results for each query in one call",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of query strings. Include multiple complementary search queries in a single call.",
                }
            },
            "required": ["query"],
        },
    },
}

_GOOGLE_SCHOLAR_TOOL = {
    "type": "function",
    "function": {
        "name": "google_scholar",
        "description": "Leverage Google Scholar to retrieve relevant information from academic publications. Accepts multiple queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "minItems": 1,
                    "description": "The list of search queries for Google Scholar.",
                }
            },
            "required": ["query"],
        },
    },
}

_VISIT_TOOL = {
    "type": "function",
    "function": {
        "name": "visit",
        "description": "Visit webpage(s) and return the summary of the content.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": ["string", "array"],
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "The URL(s) of the webpage(s) to visit. Can be a single URL or an array of URLs.",
                },
                "goal": {
                    "type": "string",
                    "description": "The goal of the visit for webpage(s).",
                },
            },
        },
        "required": ["url", "goal"],
    },
}

_UPDATE_CONTEXT_TOOL = {
    "type": "function",
    "function": {
        "name": "update_context",
        "description": """This tool allows you to compress your memory into a new `context` to maintain long-term focus and avoid context window exhaustion.
**When to use this tool:**
1. **Context Saturation:** When the conversation history becomes too long, threatening the token limit.
2. **Loss of Focus:** When the current search trajectory is cluttered with irrelevant data or the reasoning path has become confusing.
3. **Milestone Reached:** After completing a significant sub-task, to solidify progress before moving to the next phase.

**Strict Standards for new `context`:**
When calling `update_context`, the `context` parameter string MUST be a high-density, lossless distillation of all the current messages. It must replace the deleted history with actionable intelligence. You must include:
* **Confirmed Knowledge with Citations:** You MUST retain the `url` for each fact you preserve.** If you lose the `url` now, you will fail the final verification step. Use the format: `[Fact statement] (Verified in: url)`.
* **Current State & Next Steps:** Where exactly are we in the problem-solving process and a precise plan for the refreshed context.
You can also include (but not necessary):
* **Negative Constraints:** Explicitly state what has been tried and FAILED to prevent repetition.

* **Limitation:** The `update_context` function can only be called separately; do not call `update_context` function and other fucntions at the same time. 

**Critical:** You should aim to solve the problem in a single pass if possible. However, if the task requires extended reasoning, apply this tool strategically. Do not overuse it; "over-cleaning" can lead to loss of subtle details. Aim for maximum information density with minimum token usage.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "a high-density, loss-less distillation of the current state include **Confirmed Knowledge with Citations** and **Current State**.",
                }
            },
            "required": ["context"],
        },
    },
}

_FINISH_TOOL = {
    "type": "function",
    "function": {
        "name": "finish",
        "description": "Return the final result when you have a definitive answer. This function signals that your research is complete and you're ready to present the final answer to the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "A succinct, final answer to the user's query",
                },
                "evidences": {
                    "type": "array",
                    "description": "Array of evidence objects supporting the final answer. Each piece of evidence must cite exactly **one** `url`. If a fact is supported by multiple documents, choose the most authoritative one.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "evidence": {
                                "type": "string",
                                "description": "The specific verified fact or data point (one sentence)",
                            },
                            "url": {
                                "type": "string",
                                "description": "The source URL of the evidence",
                            },
                        },
                        "required": ["evidence", "url"],
                    },
                },
                "confidence": {
                    "type": "string",
                    "description": " Your confidence score between 0% and 100% for your answer",
                },
            },
            "required": ["answer", "evidences", "confidence"],
        },
    },
}


BROWSECOMP_TOOLS = (
    _SEARCH_TOOL,
    _GOOGLE_SCHOLAR_TOOL,
    _VISIT_TOOL,
    _UPDATE_CONTEXT_TOOL,
    _FINISH_TOOL,
)


def _format_tool_description(tools: tuple[dict, ...]) -> str:
    body = "<tools>\n"
    body += "".join(
        json.dumps(tool, indent=2, ensure_ascii=False) + "\n"
        for tool in tools
    )
    return body + "</tools>\n"


BROWSECOMP_SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE.format(
    tool_des=_format_tool_description(BROWSECOMP_TOOLS)
)
BROWSECOMP_USER_PROMPT = _USER_PROMPT_TEMPLATE


def build_messages(question: str) -> list[dict[str, str]]:
    """Return the initial system/user messages for one BrowseComp agent run."""

    return [
        {"role": "system", "content": BROWSECOMP_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": BROWSECOMP_USER_PROMPT.format(question=question),
        },
    ]


__all__ = [
    "BROWSECOMP_SYSTEM_PROMPT",
    "BROWSECOMP_USER_PROMPT",
    "build_messages",
]
