import asyncio
import json

import httpx

from mymanah.config import Settings
from mymanah.models import Models
from mymanah.schemas import SummaryDraft


def test_generation_constrains_quotes_without_duplicating_them_in_prompt():
    quotes = ["I completed the task and feel pleased."]
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"done": True, "done_reason": "stop", "response": json.dumps({
            "sentences": [{"text": "I completed the task.", "quote": quotes[0]},
                          {"text": "I feel pleased.", "quote": quotes[0]}]})})

    async def run():
        models = Models(Settings())
        await models.http.aclose()
        models.http = httpx.AsyncClient(base_url="http://127.0.0.1:11434", transport=httpx.MockTransport(respond))
        try:
            result = await models.generate("Summarize.", json.dumps({"source_quotes": quotes}), SummaryDraft,
                                           source_quotes=quotes)
            assert len(result.sentences) == 2
        finally:
            await models.close()

    asyncio.run(run())
    assert captured[0]["format"]["$defs"]["SummarySentence"]["properties"]["quote"]["enum"] == quotes
    prompt_schema = json.loads(captured[0]["prompt"])["output_schema"]
    assert "enum" not in prompt_schema["$defs"]["SummarySentence"]["properties"]["quote"]
    assert "enum" not in SummaryDraft.model_json_schema()["$defs"]["SummarySentence"]["properties"]["quote"]
