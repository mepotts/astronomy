"""Counts-only GitHub notifications. Uses the workflow token; no external accounts.

The dedicated issue's bot-authored comments are the durable delivery ledger.
Never save advanced watcher cache after this command fails. No POST retries:
a later invocation checks the ledger before posting again.
"""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = 'mepotts/astronomy'
MARKER = re.compile(r'<!-- ITF_NOTIFY_V1 (\{[^\n]+\}) -->')


def plan(env, comments):
    states = []
    for comment in comments:
        if comment.get('user', {}).get('login') != 'github-actions[bot]':
            continue
        found = MARKER.search(comment.get('body') or '')
        if found:
            value = json.loads(found[1])
            if set(value) != {'event', 'health', 'candidate', 'baseline'} or value['health'] not in ('ok', 'problem'):
                raise ValueError('Invalid bot ledger')
            states.append(value)
    previous = states[-1] if states else None
    ok = env.get('WATCH_OUTCOME') == 'success' and env.get('FRESHNESS_ALERT') == 'false'
    health = 'ok' if ok else 'problem'
    candidate = previous['candidate'] if previous else None
    baseline = previous['baseline'] if previous else None
    reasons = []
    first = env.get('FIRST_RUN') == 'true'
    if not previous:
        reasons.append('ITF notification setup: daily counts-only monitoring is connected.')
    if not previous or previous['health'] != health:
        reasons.append('Daily archive/watch check is healthy.' if ok else
                       'Daily archive/watch check needs attention: stale data or a failed check. No discovery inferred.')
    if ok:
        counts = {}
        for key in ('READY', 'HELD', 'NEW_READY'):
            raw = env.get(key, '')
            if not re.fullmatch(r'\d{1,7}', raw):
                raise ValueError('Invalid counts')
            counts[key] = int(raw)
        key = env.get('CANDIDATE_EVENT_KEY', '')
        if not re.fullmatch(r'[0-9a-f]{64}', key):
            raise ValueError('Invalid event key')
        seen = {s['candidate'] for s in states}
        if first:
            snapshot = env.get('SNAPSHOT', '')
            if not re.fullmatch(r'\d{8}T\d{6}Z', snapshot):
                raise ValueError('Invalid baseline snapshot')
            current_baseline = hashlib.sha256((key+snapshot).encode()).hexdigest()
            if previous and current_baseline != baseline:
                reasons.append('Watcher baseline was rebuilt (cache missing). Changes across that gap cannot be established.')
            baseline = current_baseline
        if not first and counts['NEW_READY'] > 0 and key not in seen:
            candidate = key
            reasons.append(f"Candidate review: {counts['NEW_READY']} newly ready. NOT confirmed discoveries.")
        if reasons:
            reasons.append(f"Current queue: {counts['READY']} ready / {counts['HELD']} held.")
    if not reasons:
        return None
    # Stable across retry of one observation; new incident gets a distinct predecessor.
    event = hashlib.sha256(json.dumps([previous, health, candidate, baseline, reasons], sort_keys=True).encode()).hexdigest()
    if any(s['event'] == event for s in states):
        return None
    state = {'event': event, 'health': health, 'candidate': candidate, 'baseline': baseline}
    run_id = env.get('GITHUB_RUN_ID', '')
    if not re.fullmatch(r'\d+', run_id):
        raise ValueError('Invalid run ID')
    return ('@mepotts\n\n'+'\n\n'.join(reasons)+
            '\n\nNo candidate identifiers or coordinates disclosed. No MPC submission made.\n\n'+
            f'[Daily run](https://github.com/{REPO}/actions/runs/{run_id})\n\n'+
            '<!-- ITF_NOTIFY_V1 '+json.dumps(state, sort_keys=True)+' -->')


def api(method, path, token, body=None):
    raw = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request('https://api.github.com'+path, data=raw, method=method,
        headers={'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=25) as response:
        raw = response.read(2*1024*1024+1)
        if len(raw) > 2*1024*1024:
            raise ValueError('Response limit')
        return json.loads(raw)


def main(env=None):
    env = os.environ if env is None else env
    if env.get('GITHUB_REPOSITORY') != REPO:
        raise ValueError('Wrong repository')
    issue = env.get('ITF_ALERT_ISSUE', '')
    if not re.fullmatch(r'[1-9]\d*', issue):
        raise ValueError('Configure the fixed ITF alert issue first')
    token = env['GH_TOKEN']
    base = f'/repos/{REPO}/issues/{issue}'
    target = api('GET', base, token)
    if target.get('title') != 'ITF daily alerts' or 'pull_request' in target or target.get('state') != 'open':
        raise ValueError('Unexpected alert destination')
    comments = []
    for page in range(1, 51):
        batch = api('GET', base+f'/comments?per_page=100&page={page}', token)
        if not isinstance(batch, list):
            raise TypeError('Invalid comments response')
        comments.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError('Ledger pagination limit; do not silently discard history')
    body = plan(env, comments)
    if body:
        receipt = api('POST', base+'/comments', token, {'body': body})
        if type(receipt.get('id')) is not int or receipt.get('body') != body:
            raise ValueError('Unverified comment acceptance')
        print('Counts-only alert posted; email/push delivery depends on user settings.')
    else:
        print('No new alert; unchanged state or already reported.')


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa: BLE001 -- never echo server bodies, tokens or private input
        print('GitHub alert failed; watcher cache must not advance.', file=sys.stderr)
        raise SystemExit(1) from None
