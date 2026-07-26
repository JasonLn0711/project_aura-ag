# ChatGPT Login Guide

## Provider-managed login

Live mode reads account state from Codex app-server. When the account is signed
out:

1. select **Live**;
2. wait for the local Codex process to initialize;
3. select **Sign in with ChatGPT**;
4. AURA calls `account/login/start` with the observed `chatgpt` schema;
5. AURA opens the returned authorization URL with the injected system-browser
   opener;
6. complete provider authorization in the browser;
7. app-server emits login/account updates;
8. AURA refreshes the non-secret account status and model list.

Device-code login calls the advertised `chatgptDeviceCode` variant and shows
the verification URL and one-time user code.

## Credential stewardship

Codex app-server owns credentials. AURA does not read `auth.json`, copy
`CODEX_HOME`, parse keychains, receive OAuth tokens, persist tokens, log
tokens, export tokens, or expose account email. It retains only status,
account type, plan type when supplied, attempt state, provider version, and
timestamps.

API-key mode is not required for this release. A local ChatGPT login is a single-user
desktop boundary. Hosted multi-user service requires per-user identity,
isolated credentials, tenant policy, usage ownership, revocation, and a
separate threat model.

## Recovery

A failed or expired attempt keeps AURA signed out. Retry ChatGPT login, choose
device code, return to Demo, or cancel. AURA stores no partial credential
state.
