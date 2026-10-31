#!/usr/bin/env python3
"""MCP server (stdio) over the trainer's content: questions, weed atlas, MK noteikumi Nr. 950.

Lets Claude Code / Claude Desktop answer questions about the course material. No API key and
no third-party packages are needed: the client's own model does the reasoning, this server
only searches and returns the content. Register it with .mcp.json (Claude Code) or
claude_desktop_config.json ("command": "python3", "args": ["<repo>/scripts/mcp_server.py"]).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge

KINDS = ['question', 'weed', 'biological_group', 'root_system', 'root_type', 'weed_photo', 'mk950_point']

TOOLS = [
    dict(name='search', description=(
        'Meklē visā VAAD AAL trenažiera saturā (jautājumi ar atbildēm un skaidrojumiem, nezāļu atlants, '
        'bioloģiskās grupas, sakņu sistēmas, MK noteikumu Nr. 950 punkti). Vaicājumu raksti latviski; '
        'garumzīmes nav obligātas. Search all trainer content; returns best matches with sources.'),
        inputSchema=dict(type='object', properties=dict(
            query=dict(type='string', description='Atslēgvārdi, piem. "vēja ātrums smidzināšana" vai "ložņu vārpata"'),
            kinds=dict(type='array', items=dict(type='string', enum=KINDS), description='Neobligāti: ierobežot satura veidus'),
            limit=dict(type='integer', minimum=1, maximum=30, default=10)),
            required=['query'], additionalProperties=False)),
    dict(name='mk950_point', description=(
        'Atgriež MK 13.12.2011. noteikumu Nr. 950 „Augu aizsardzības līdzekļu lietošanas noteikumi” '
        'punkta pilnu tekstu ar apakšpunktiem (piem. "18" vai "18.1"; iestarpinātie punkti "13¹", "21¹", "41¹").'),
        inputSchema=dict(type='object', properties=dict(point=dict(type='string')), required=['point'], additionalProperties=False)),
    dict(name='list_topics', description='Trenažiera tēmas un jautājumu skaits katrā.',
         inputSchema=dict(type='object', properties={}, additionalProperties=False)),
    dict(name='topic_questions', description='Tēmas jautājumi ar pareizajām atbildēm un skaidrojumiem (lapošana ar offset).',
         inputSchema=dict(type='object', properties=dict(
             topic=dict(type='string'), limit=dict(type='integer', minimum=1, maximum=100, default=30),
             offset=dict(type='integer', minimum=0, default=0)), required=['topic'], additionalProperties=False)),
    dict(name='get_question', description='Viens jautājums pēc ID (piem. "MK950-033") ar atbildi un skaidrojumu.',
         inputSchema=dict(type='object', properties=dict(id=dict(type='string')), required=['id'], additionalProperties=False)),
    dict(name='quiz', description='Nejauši teksta jautājumi BEZ atbildēm pārbaudei (var norādīt tēmu). Atbildi pārbauda ar check_answer.',
         inputSchema=dict(type='object', properties=dict(
             topic=dict(type='string'), count=dict(type='integer', minimum=1, maximum=20, default=5)), additionalProperties=False)),
    dict(name='check_answer', description='Pārbauda lietotāja atbildi uz jautājumu pēc ID un atgriež pareizo atbildi ar skaidrojumu.',
         inputSchema=dict(type='object', properties=dict(id=dict(type='string'), answer=dict(type='string')),
                          required=['id', 'answer'], additionalProperties=False)),
    dict(name='overview', description='Trenažiera satura kopsavilkums un avotu saraksts.',
         inputSchema=dict(type='object', properties={}, additionalProperties=False)),
]


def call_tool(name, args):
    if name == 'search':
        return knowledge.search(args['query'], kinds=args.get('kinds'), limit=args.get('limit', 10))
    if name == 'mk950_point':
        return knowledge.mk950_point(args['point']) or {'error': f"Punkts {args['point']} nav atrasts"}
    if name == 'list_topics':
        return knowledge.topics()
    if name == 'topic_questions':
        return knowledge.topic_questions(args['topic'], args.get('limit', 30), args.get('offset', 0))
    if name == 'get_question':
        return knowledge.get_question(args['id']) or {'error': f"Jautājums {args['id']} nav atrasts"}
    if name == 'quiz':
        return knowledge.quiz(args.get('topic'), args.get('count', 5))
    if name == 'check_answer':
        return knowledge.check_answer(args['id'], args['answer']) or {'error': f"Jautājums {args['id']} nav atrasts"}
    if name == 'overview':
        return knowledge.overview()
    raise KeyError(name)


def handle(msg):
    method, params = msg.get('method'), msg.get('params') or {}
    if method == 'initialize':
        return dict(protocolVersion=params.get('protocolVersion', '2025-06-18'),
                    capabilities=dict(tools={}),
                    serverInfo=dict(name='vaad-aal-trenazieris', version='1.0.0'),
                    instructions='VAAD AAL 2. klases trenažiera saturs. Atbildot balsties uz rīku rezultātiem un norādīt avotu '
                                 '(piem. MK Nr. 950 punktu). Šis nav oficiāls VAAD eksāmens.')
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return dict(tools=TOOLS)
    if method == 'tools/call':
        try:
            result = call_tool(params['name'], params.get('arguments') or {})
        except KeyError as e:
            return dict(content=[dict(type='text', text=f'Nezināms rīks vai trūkst parametra: {e}')], isError=True)
        return dict(content=[dict(type='text', text=json.dumps(result, ensure_ascii=False, indent=1))])
    raise LookupError(method)


def main():
    knowledge.documents()  # build the index before the first request
    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        if 'id' not in msg:  # notification (e.g. notifications/initialized)
            continue
        try:
            reply = dict(jsonrpc='2.0', id=msg['id'], result=handle(msg))
        except LookupError:
            reply = dict(jsonrpc='2.0', id=msg['id'], error=dict(code=-32601, message=f"Method not found: {msg.get('method')}"))
        except Exception as e:
            reply = dict(jsonrpc='2.0', id=msg['id'], error=dict(code=-32603, message=str(e)))
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
