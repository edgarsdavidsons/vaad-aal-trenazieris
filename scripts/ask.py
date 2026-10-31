#!/usr/bin/env python3
"""Ask Claude about the trainer's content from the terminal.

Claude answers using the same tools as the MCP server (search, MK Nr. 950 points, quiz ...).
The API key is read from ANTHROPIC_API_KEY (or an `ant auth login` profile) – never put it in
this repository: the site is public on GitHub Pages.

  .venv/bin/pip install anthropic
  export ANTHROPIC_API_KEY=...
  .venv/bin/python scripts/ask.py "Pie kāda vēja ātruma drīkst smidzināt?"
  .venv/bin/python scripts/ask.py            # interactive chat, empty line to quit
"""
import json, sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_server import TOOLS, call_tool

MODEL = 'claude-opus-5-5'
SYSTEM = (
    'Tu esi VAAD augu aizsardzības līdzekļu (AAL) 2. reģistrācijas klases lietotāju mācību asistents. '
    'Atbildi latviski, ja vien lietotājs nejautā citā valodā. Faktus ņem no rīku rezultātiem (trenažiera '
    'jautājumi, nezāļu atlants, MK noteikumi Nr. 950); pirms atbildes meklē, un norādi avotu, piem. „MK Nr. 950, 18.1. punkts”. '
    'Ja rīki neko neatrod, saki to, nevis min. Atgādini, ka trenažieris nav oficiāls VAAD eksāmens, tikai ja tas ir svarīgi. '
    'Ja lietotājs grib pārbaudīt zināšanas, izmanto quiz un check_answer un nerādi atbildi pirms lietotājs atbildējis.'
)
API_TOOLS = [dict(name=t['name'], description=t['description'], input_schema=t['inputSchema']) for t in TOOLS]


def run_turn(client, messages):
    """Run Claude until it stops calling tools; append everything to messages; return the answer text."""
    while True:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=API_TOOLS,
            messages=messages,
            thinking={'type': 'adaptive'},
            output_config={'effort': 'medium'},
            betas=['server-side-fallback-2026-07-01'],
            fallbacks='default',
        )
        messages.append({'role': 'assistant', 'content': response.content})
        if response.stop_reason == 'refusal':
            return '(Modelis atteicās atbildēt uz šo jautājumu.)'
        if response.stop_reason == 'pause_turn':
            continue
        tool_uses = [b for b in response.content if b.type == 'tool_use']
        if not tool_uses:
            return ''.join(b.text for b in response.content if b.type == 'text')
        results = []
        for block in tool_uses:
            print(f'  · {block.name}({json.dumps(block.input, ensure_ascii=False)})', file=sys.stderr)
            try:
                content, is_error = json.dumps(call_tool(block.name, block.input), ensure_ascii=False), False
            except Exception as e:
                content, is_error = f'Kļūda: {e}', True
            results.append({'type': 'tool_result', 'tool_use_id': block.id, 'content': content, 'is_error': is_error})
        messages.append({'role': 'user', 'content': results})


def main():
    client = anthropic.Anthropic()
    messages = []
    question = ' '.join(sys.argv[1:]).strip()
    interactive = not question
    while True:
        if interactive:
            try:
                question = input('\nJautājums: ').strip()
            except EOFError:
                return
            if not question:
                return
        start = len(messages)
        messages.append({'role': 'user', 'content': question})
        try:
            print('\n' + run_turn(client, messages))
        except anthropic.AuthenticationError:
            sys.exit('API atslēga nav derīga. Iestati ANTHROPIC_API_KEY (Claude Console API atslēga, sk-ant-api...).')
        except anthropic.RateLimitError:
            print('Pārsniegts pieprasījumu limits, pamēģini vēlreiz pēc brīža.', file=sys.stderr)
            del messages[start:]
        except anthropic.APIConnectionError as e:
            print(f'Nav savienojuma ar API: {e}', file=sys.stderr)
            del messages[start:]
        if not interactive:
            return


if __name__ == '__main__':
    main()
