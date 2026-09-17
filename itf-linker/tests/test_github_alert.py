"""No live API calls. Counts-only event and retry regression tests."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('github_itf_alert', Path(__file__).resolve().parents[1]/'scripts/github_itf_alert.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def env(**extra):
    return {'WATCH_OUTCOME': 'success', 'FRESHNESS_ALERT': 'false', 'FIRST_RUN': 'false',
            'READY': '18', 'HELD': '8', 'NEW_READY': '0', 'CANDIDATE_EVENT_KEY': 'a'*64,
            'SNAPSHOT': '20260917T212636Z', 'GITHUB_RUN_ID': '123', **extra}


def comment(body, author='github-actions[bot]'):
    return {'user': {'login': author}, 'body': body}


def test_enrollment_healthy_and_retry_quiet():
    e = env(FIRST_RUN='true')
    body = m.plan(e, [])
    assert '@mepotts' in body and '18 ready / 8 held' in body
    assert m.plan(e, [comment(body)]) is None
    assert m.plan(env(), [comment(body)]) is None


def test_candidate_retry_same_transition_later_snapshot_quiet():
    baseline = comment(m.plan(env(FIRST_RUN='true'), []))
    e = env(NEW_READY='2', READY='20', CANDIDATE_EVENT_KEY='b'*64)
    body = m.plan(e, [baseline])
    assert '2 newly ready' in body and 'NOT confirmed discoveries' in body
    assert m.plan(e, [baseline, comment(body)]) is None
    assert m.plan({**e, 'SNAPSHOT': '20260918T212636Z'}, [baseline, comment(body)]) is None


def test_health_incident_repeated_and_recovery():
    first = comment(m.plan(env(), []))
    bad = env(WATCH_OUTCOME='failure', NEW_READY='secret')
    body = m.plan(bad, [first])
    assert 'needs attention' in body and 'secret' not in body
    assert m.plan(bad, [first, comment(body)]) is None
    recovery = m.plan(env(), [first, comment(body)])
    assert 'healthy' in recovery


def test_stale_data_never_candidate_alert():
    body = m.plan(env(FRESHNESS_ALERT='true', NEW_READY='9'), [])
    assert 'newly ready' not in body


def test_cache_loss_reported_once_without_false_candidates():
    baseline = comment(m.plan(env(FIRST_RUN='true'), []))
    e = env(FIRST_RUN='true', NEW_READY='18', SNAPSHOT='20260918T212636Z')
    body = m.plan(e, [baseline])
    assert 'cache missing' in body and 'newly ready' not in body
    assert m.plan(e, [baseline, comment(body)]) is None


def test_untrusted_comments_do_not_suppress_notifications():
    body = m.plan(env(), [])
    assert m.plan(env(), [comment(body, 'untrusted-user')]) is not None


@pytest.mark.parametrize('key,value', [('READY','private-candidate'),('CANDIDATE_EVENT_KEY','secret'),('GITHUB_RUN_ID','123\n@someone')])
def test_unexpected_input_fails_closed(key, value):
    with pytest.raises(ValueError):
        m.plan(env(**{key: value}), [])


def test_main_fails_closed_before_post_on_wrong_issue(monkeypatch):
    calls = []
    def api(method, path, token, body=None):
        calls.append(method)
        return {'title': 'wrong', 'state': 'open'}
    monkeypatch.setattr(m, 'api', api)
    with pytest.raises(ValueError):
        m.main(env(GITHUB_REPOSITORY='mepotts/astronomy', ITF_ALERT_ISSUE='1', GH_TOKEN='test'))
    assert calls == ['GET']


def test_api_failure_does_not_retry_post(monkeypatch):
    calls = []
    def api(method, path, token, body=None):
        calls.append(method)
        if method == 'POST':
            raise OSError('private response')
        return [] if '/comments?' in path else {'title': 'ITF daily alerts', 'state': 'open'}
    monkeypatch.setattr(m, 'api', api)
    with pytest.raises(OSError):
        m.main(env(GITHUB_REPOSITORY='mepotts/astronomy', ITF_ALERT_ISSUE='1', GH_TOKEN='test'))
    assert calls.count('POST') == 1
