import json
import sys
import time


THREAD_ID = "019f0000-0000-7000-8000-000000000001"
TURN_ID = "019f0000-0000-7000-8000-000000000002"
APPROVAL_RPC_ID = 9001
pending_approval = False
experimental_api = False
MODE = sys.argv[1] if len(sys.argv) > 1 else "normal"
signed_in = MODE != "signed-out"


def send(message, *, fragmented=False):
    encoded = json.dumps(message, separators=(",", ":"))
    if fragmented:
        midpoint = len(encoded) // 2
        sys.stdout.write(encoded[:midpoint])
        sys.stdout.flush()
        time.sleep(0.01)
        sys.stdout.write(encoded[midpoint:] + "\n")
    else:
        sys.stdout.write(encoded + "\n")
    sys.stdout.flush()


def complete_turn():
    if MODE not in {"no-summary", "empty-summary"}:
        send(
            {
                "method": "item/reasoning/summaryTextDelta",
                "params": {
                    "threadId": THREAD_ID,
                    "turnId": TURN_ID,
                    "itemId": "reasoning-1",
                    "summaryIndex": 0,
                    "delta": "已確認 Repository 範圍與唯讀執行設定。",
                },
            }
        )
    if MODE != "no-summary":
        send(
            {
                "method": "item/completed",
                "params": {
                    "threadId": THREAD_ID,
                    "turnId": TURN_ID,
                    "completedAtMs": 1,
                    "item": {
                        "id": "reasoning-1",
                        "type": "reasoning",
                        "summary": (
                            []
                            if MODE in {"empty-summary", "delta-empty-summary"}
                            else ["已確認 Repository 範圍與唯讀執行設定。"]
                        ),
                    },
                },
            }
        )
    send(
        {
            "method": "item/agentMessage/delta",
            "params": {
                "threadId": THREAD_ID,
                "turnId": TURN_ID,
                "itemId": "message-1",
                "delta": "Read-only review complete.",
            },
        }
    )
    send(
        {
            "method": "item/completed",
            "params": {
                "threadId": THREAD_ID,
                "turnId": TURN_ID,
                "completedAtMs": 1,
                "item": {
                    "id": "message-1",
                    "type": "agentMessage",
                    "text": "Read-only review complete.",
                },
            },
        }
    )
    send(
        {
            "method": "turn/completed",
            "params": {
                "threadId": THREAD_ID,
                "turn": {
                    "id": TURN_ID,
                    "status": "completed",
                    "items": [],
                    "startedAt": 1,
                    "completedAt": 2,
                },
            },
        }
    )


for raw in sys.stdin:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        continue
    if "method" not in message and message.get("id") == APPROVAL_RPC_ID:
        pending_approval = False
        complete_turn()
        continue
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialized":
        continue
    if method == "test/fragmented":
        send({"id": request_id, "result": {"ok": True}}, fragmented=True)
    elif method == "test/multiple":
        messages = (
            {"method": "fixture/one", "params": {"value": 1}},
            {"method": "fixture/two", "params": {"value": 2}},
            {"id": request_id, "result": {"count": 2}},
        )
        sys.stdout.write(
            "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in messages)
        )
        sys.stdout.flush()
    elif method == "test/error":
        send(
            {
                "id": request_id,
                "error": {"code": -32000, "message": "fixture failure"},
            }
        )
    elif method == "test/timeout":
        continue
    elif method == "test/oversized":
        send({"id": request_id, "result": {"text": "x" * 4096}})
    elif method == "test/crash":
        sys.exit(7)
    elif method == "test/invalid":
        sys.stdout.write("{invalid json}\n")
        sys.stdout.flush()
    elif method == "initialize":
        if MODE == "no-initialize":
            continue
        experimental_api = bool(
            (params.get("capabilities") or {}).get("experimentalApi")
        )
        send(
            {
                "id": request_id,
                "result": {
                    "userAgent": "codex-cli/0.145.0",
                    "platformFamily": "unix",
                    "platformOs": "linux",
                    "codexHome": "/redacted",
                },
            }
        )
    elif method == "account/read":
        send(
            {
                "id": request_id,
                "result": {
                    "account": (
                        {
                            "type": "chatgpt",
                            "email": "private@example.invalid",
                            "planType": "plus",
                        }
                        if signed_in
                        else None
                    ),
                    "requiresOpenaiAuth": True,
                },
            }
        )
    elif method == "account/login/start":
        login_type = params.get("type")
        if login_type == "chatgptDeviceCode":
            result = {
                "type": login_type,
                "loginId": "login-1",
                "verificationUrl": "https://example.invalid/device",
                "userCode": "SAFE-CODE",
            }
        else:
            result = {
                "type": "chatgpt",
                "loginId": "login-1",
                "authUrl": "https://example.invalid/login",
            }
        send({"id": request_id, "result": result})
        if MODE == "signed-out":
            signed_in = True
            send(
                {
                    "method": "account/login/completed",
                    "params": {"loginId": "login-1", "success": True},
                }
            )
    elif method == "account/logout":
        signed_in = False
        send({"id": request_id, "result": {}})
    elif method == "account/login/cancel":
        send({"id": request_id, "result": {}})
    elif method == "model/list":
        model_id = "gpt-4.1" if MODE == "no-sol" else "gpt-5.6-sol"
        send(
            {
                "id": request_id,
                "result": {
                    "data": [
                        {
                            "id": model_id,
                            "model": model_id,
                            "displayName": model_id,
                            "description": "Fake schema fixture",
                            "supportedReasoningEfforts": [
                                {"reasoningEffort": value, "description": value}
                                for value in ("low", "medium", "high", "xhigh", "max", "ultra")
                            ],
                            "defaultReasoningEffort": "medium",
                            "isDefault": True,
                            "hidden": False,
                            "serviceTiers": [{"id": "priority", "displayName": "Priority"}],
                        }
                    ],
                    "nextCursor": None,
                },
            }
        )
    elif method == "thread/list":
        if MODE == "no-probe":
            send(
                {
                    "id": request_id,
                    "error": {"code": -32601, "message": "thread/list unavailable"},
                }
            )
        else:
            send({"id": request_id, "result": {"data": [], "nextCursor": None}})
    elif method == "thread/read":
        send(
            {
                "id": request_id,
                "result": {"thread": {"id": params["threadId"], "turns": []}},
            }
        )
    elif method == "thread/archive":
        send({"id": request_id, "result": {}})
    elif (
        method in {"thread/start", "thread/resume"}
        and params.get("runtimeWorkspaceRoots")
        and not experimental_api
    ):
        send(
            {
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": (
                        f"{method}.runtimeWorkspaceRoots requires "
                        "experimentalApi capability"
                    ),
                },
            }
        )
    elif method == "thread/start":
        thread = {
            "id": THREAD_ID,
            "preview": "",
            "ephemeral": False,
            "modelProvider": "openai",
            "createdAt": 1,
            "updatedAt": 1,
            "status": {"type": "idle"},
            "path": "/redacted",
            "cwd": params.get("cwd"),
            "cliVersion": "0.145.0",
            "source": "appServer",
            "agentNickname": None,
            "agentRole": None,
            "gitInfo": None,
            "turns": [],
        }
        send(
            {
                "id": request_id,
                "result": {
                    "thread": thread,
                    "model": params.get("model"),
                    "modelProvider": "openai",
                    "cwd": params.get("cwd"),
                    "approvalPolicy": "on-request",
                    "approvalsReviewer": "user",
                    "sandbox": {"type": "readOnly", "networkAccess": False},
                    "reasoningEffort": "max",
                    "instructionSources": [
                        f"{params.get('cwd')}/AGENTS.md",
                        "/provider-profile/.codex/AGENTS.md",
                    ],
                },
            }
        )
        send({"method": "thread/started", "params": {"thread": thread}})
    elif method == "thread/resume":
        send(
            {
                "id": request_id,
                "result": {
                    "thread": {"id": params["threadId"], "turns": []},
                    "model": "gpt-5.6-sol",
                    "modelProvider": "openai",
                    "cwd": ".",
                    "approvalPolicy": "on-request",
                    "approvalsReviewer": "user",
                    "sandbox": {"type": "readOnly", "networkAccess": False},
                },
            }
        )
    elif method == "turn/start":
        if MODE == "write-contract":
            expected_policy = {
                "type": "workspaceWrite",
                "writableRoots": [params.get("cwd")],
                "networkAccess": False,
            }
            if params.get("sandboxPolicy") != expected_policy:
                send(
                    {
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "workspace-write turn policy mismatch",
                        },
                    }
                )
                continue
        turn = {
            "id": TURN_ID,
            "status": "inProgress",
            "items": [],
            "startedAt": 1,
            "completedAt": None,
        }
        send({"id": request_id, "result": {"turn": turn}})
        send(
            {
                "method": "turn/started",
                "params": {"threadId": THREAD_ID, "turn": turn},
            }
        )
        task = " ".join(
            item.get("text", "") for item in params.get("input", []) if isinstance(item, dict)
        )
        if "APPROVAL" in task:
            pending_approval = True
            send(
                {
                    "id": APPROVAL_RPC_ID,
                    "method": "item/commandExecution/requestApproval",
                    "params": {
                        "threadId": THREAD_ID,
                        "turnId": TURN_ID,
                        "itemId": "command-1",
                        "startedAtMs": 1,
                        "command": "git status --short",
                        "cwd": params.get("cwd"),
                        "reason": "Confirm read-only inspection.",
                        "availableDecisions": ["accept", "decline", "cancel"],
                    },
                }
            )
        elif "TEST" in task:
            send(
                {
                    "method": "item/completed",
                    "params": {
                        "threadId": THREAD_ID,
                        "turnId": TURN_ID,
                        "item": {
                            "id": "command-test",
                            "type": "commandExecution",
                            "command": "python -m unittest",
                            "cwd": params.get("cwd"),
                            "exitCode": 0,
                            "durationMs": 25,
                            "aggregatedOutput": "OK",
                        },
                    },
                }
            )
            complete_turn()
        else:
            complete_turn()
    elif method == "turn/interrupt":
        send({"id": request_id, "result": {}})
        send(
            {
                "method": "turn/completed",
                "params": {
                    "threadId": params["threadId"],
                    "turn": {
                        "id": params["turnId"],
                        "status": "interrupted",
                        "items": [],
                        "startedAt": 1,
                        "completedAt": 2,
                    },
                },
            }
        )
    elif method == "turn/steer":
        send({"id": request_id, "result": {"turnId": params["expectedTurnId"]}})
    elif request_id is not None:
        send(
            {
                "id": request_id,
                "error": {"code": -32601, "message": f"unknown method: {method}"},
            }
        )
