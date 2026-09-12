# ITF automation and notification audit

**Daily archive/watch: yes. Guaranteed discovery text/email: no.**
Read-only audit on September 12; no notification settings or recipients changed.

| Component | What actually runs | What reaches the user |
|---|---|---|
| Windows `ITF snapshot (daily)` | Acquires and publishes the archive/key set; owner-context scheduler inspection showed last result 0 and next run September 13 at 08:30 local. | No dedicated SMS/email sender was verified. The computer/task must run. |
| GitHub `ITF submission watch` | Daily at 15:00 UTC; consumes the published key set, rechecks the existing committed review queue and snapshot freshness. | Counts-only job summary and workflow annotations. A stale snapshot fails the job. |
| Codex portfolio follow-up | Active weekly Saturday 11:30 local; reports meaningful changes, failures or required action. | In-app follow-up; desktop/OS delivery preferences were not verified. Not an immediate daily discovery alert. |

The [actual workflow](../.github/workflows/itf-submission-watch.yml) contains no
SMS, email, webhook, issue or comment sender. Successful queue movement emits a
GitHub `notice`, which is **not proof of email/push delivery**. GitHub workflow
emails depend on subscriptions/account preferences and, for scheduled jobs,
which account created or changed/enabled the schedule; those preferences were
not verified. See [GitHub workflow notification rules](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs).

Importantly, this daily workflow is **not a daily fresh orbital-discovery search**.
It monitors an existing queue. M14 attribution remains stopped, and a tracklet
disappearing from the ITF is not proof that our proposed identification was
confirmed. September 12's accepted recovery reports 18 ready / 8 held, not 18
discoveries. No MPC submission is automated.

## What an explicit discovery-alert implementation would need

First define the event: archive failure, queue movement, newly validated candidate,
or independently confirmed discovery. Keep these distinct. Add a durable,
deduplicated counts-only alert with retries/delivery status and a private link;
never include candidate identifiers or coordinates in public logs. Then obtain
approval for the exact recipient/channel and any test message, and prove delivery.
Account secrets belong in the platform secret store, not the repository.

No such new sender or outbound test was authorized merely by asking whether it
exists. The daily jobs and existing weekly follow-up remain unchanged. Codex
notification options and operating-system permissions are described in the
[official notification guide](https://learn.chatgpt.com/docs/notifications);
availability does not establish that a channel is enabled on this machine.
