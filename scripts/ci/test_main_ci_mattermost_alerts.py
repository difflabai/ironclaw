#!/usr/bin/env python3
"""Execute CI notification workflow callers with captured provider arguments."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MattermostWorkflowTests(unittest.TestCase):
    def run_workflow(self, name, event="push", configured=True):
        workflow = (ROOT / ".github/workflows" / name).read_text()
        script = textwrap.dedent(workflow.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as task_dir:
            directory = Path(task_dir)
            (directory / "gh").write_text("""#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
if args[:2] == ['run', 'list']:
    print(json.dumps([{'databaseId': 9, 'conclusion': 'failure', 'createdAt': '2026-11-02T00:00:00Z', 'url': 'https://github.com/example/repo/actions/runs/9'}]))
elif '--slurp' in args:
    print(json.dumps([{'jobs': [{'name': 'Unit tests', 'conclusion': 'failure', 'steps': [{'name': 'Contract test', 'conclusion': 'failure'}], 'check_run_url': 'https://api.github.com/repos/example/repo/check-runs/10'}]}]))
elif any('/annotations' in arg for arg in args):
    print('sample failure annotation @channel')
elif any('/pulls/' in arg for arg in args):
    print(json.dumps({'title': 'Fix service alerts', 'html_url': 'https://github.com/example/repo/pull/42', 'user': {'login': 'alice'}}))
else:
    print('Unit tests')
""")
            (directory / "curl").write_text("""#!/usr/bin/env python3
import json, os, sys
with open(os.environ['CAPTURE_WEBHOOK_ARGS'], 'a') as output:
    print(json.dumps(sys.argv[1:]), file=output)
""")
            for executable in (directory / "gh", directory / "curl"):
                executable.chmod(0o755)
            capture = directory / "capture.jsonl"
            env = {**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"],
                   "CAPTURE_WEBHOOK_ARGS": str(capture), "SLACK_WEBHOOK_URL": "https://old.example.test/hooks/never-used", "MAIN_CI_SLACK_WEBHOOK_URLS": "https://old.example.test/hooks/never-used", "GITHUB_REPOSITORY": "example/repo",
                   "RUN_ID": "9", "RUN_URL": "https://github.com/example/repo/actions/runs/9",
                   "WORKFLOW_NAME": "Tests", "CONCLUSION": "failure", "HEAD_SHA": "abcdef0123456789",
                   "HEAD_BRANCH": "gh-readonly-queue/main/pr-42-abcdef" if event == "merge_group" else "main",
                   "ACTOR": "alice", "EVENT_NAME": event, "WATCHED_WORKFLOW": "Nightly Deep CI",
                   "REPO": "example/repo", "MAX_AGE_SECONDS": "93600",
                   "MAIN_CI_MATTERMOST_WEBHOOK_URLS": "https://chat.example.test/hooks/main-a,https://chat.example.test/hooks/main-b" if configured else "",
                   "LIVE_CANARY_MATTERMOST_WEBHOOK_URL": "https://chat.example.test/hooks/canary" if configured else "",
                   "MATTERMOST_WEBHOOK_URL": "https://chat.example.test/hooks/canary" if configured else ""}
            result = subprocess.run(["bash", "-c", script], env=env, cwd=directory, capture_output=True, text=True)
            calls = [json.loads(line) for line in capture.read_text().splitlines()] if capture.exists() else []
            return result, calls

    def assert_native_payload(self, call):
        payload = json.loads(call[call.index("--data") + 1])
        self.assertEqual(set(payload), {"text"})
        self.assertIn("**", payload["text"])
        self.assertNotIn("<https://", payload["text"])
        self.assertNotIn("\\n", payload["text"])
        return payload["text"]

    def test_main_failure_fanout_contains_failed_steps_annotations_and_run_link(self):
        result, calls = self.run_workflow("main-ci-mattermost-alerts.yml")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 2)
        self.assertEqual([call[-1] for call in calls], ["https://chat.example.test/hooks/main-a", "https://chat.example.test/hooks/main-b"])
        for call in calls:
            text = self.assert_native_payload(call)
            self.assertIn("Contract test", text)
            self.assertIn("sample failure annotation @\u200bchannel", text)
            self.assertIn("[Open workflow run](https://github.com/example/repo/actions/runs/9)", text)
            self.assertIn("**Branch:** `main`\n**Commit:**", text)

    def test_merge_queue_alert_uses_canary_channel_and_resolves_pull_request(self):
        result, calls = self.run_workflow("main-ci-mattermost-alerts.yml", event="merge_group")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-1], "https://chat.example.test/hooks/canary")
        self.assertIn("[#42 Fix service alerts](https://github.com/example/repo/pull/42)", self.assert_native_payload(calls[0]))

    def test_unconfigured_alert_does_not_fall_back_to_slack(self):
        result, calls = self.run_workflow("main-ci-mattermost-alerts.yml", configured=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn("MAIN_CI_MATTERMOST_WEBHOOK_URLS", result.stdout)

    def test_watchdog_posts_markdown_but_keeps_failure_in_workflow_result(self):
        result, calls = self.run_workflow("nightly-watchdog.yml")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(calls), 1)
        text = self.assert_native_payload(calls[0])
        self.assertIn("**Nightly Deep CI**", text)
        self.assertIn("[run](https://github.com/example/repo/actions/runs/9)", text)


if __name__ == "__main__":
    unittest.main()
