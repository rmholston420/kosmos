# AREX-Turbo Inference

This folder provides a minimal one-turn inference example and the complete BrowseComp prompts. It follows the XML tool-call protocol used by the public AREX evaluation code.

## Serve the model

Run the following commands from the model repository root. Recent versions of vLLM, SGLang, or another OpenAI-compatible server with Qwen3.5 support can be used. For a text-only vLLM deployment:

```bash
vllm serve . \
  --served-model-name AREX-Turbo \
  --tensor-parallel-size 1 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --language-model-only
```

Adjust the tensor-parallel size and maximum context length for your hardware.

## Run one generation

Install the client:

```bash
pip install -U openai
```

Then send a BrowseComp-style question:

```bash
export AREX_BASE_URL="http://127.0.0.1:8000/v1"
export AREX_API_KEY="EMPTY"
export AREX_MODEL="AREX-Turbo"

python inference/inference.py \
  --question "Your BrowseComp question"
```

The script returns the model's next action. When it emits an XML `<tool_call>`, execute that tool, append the assistant output to the message history, and add the real tool result as:

```text
<tool_response>
actual tool result
</tool_response>
```

Continue until the model calls `finish`. The example intentionally leaves tool execution to the caller.

## Use the prompts directly

[`prompts.py`](prompts.py) exports the BrowseComp system and user prompt constants. Tool descriptions are already embedded in the system prompt, so only the question needs formatting:

```python
from inference.prompts import (
    BROWSECOMP_SYSTEM_PROMPT,
    BROWSECOMP_USER_PROMPT,
)

question = "Your BrowseComp question"
messages = [
    {"role": "system", "content": BROWSECOMP_SYSTEM_PROMPT},
    {
        "role": "user",
        "content": BROWSECOMP_USER_PROMPT.format(question=question),
    },
]
```

`build_messages(question)` is a convenience wrapper for the same formatting.

BrowseComp exposes `search`, `google_scholar`, `visit`, `update_context`, and `finish`.
