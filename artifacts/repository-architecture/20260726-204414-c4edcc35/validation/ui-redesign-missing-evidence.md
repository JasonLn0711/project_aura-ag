# Missing Evidence and Next Validation

| ID | Status | Evidence boundary | Next validation |
| --- | --- | --- | --- |
| ME-UI-001 | `NOT VERIFIED` | Five-person task-based study, including the five-second comprehension target | Run `docs/agent-workspace/ux-redesign/09-usability-test-plan.md` with five participants and retain privacy-safe aggregate results |
| ME-UI-002 | `PARTIALLY VERIFIED` | Logical focus and accessible metadata are automated; field assistive-technology behavior is not measured | Run keyboard-only plus the selected desktop screen reader on the seven study tasks |
| ME-UI-003 | `PARTIALLY VERIFIED` | New model/view and core intent paths are bounded; several legacy Git/SQLite/report/media/provider actions still call services from presentation handlers | Move each remaining action behind typed background service execution and add a GUI-heartbeat regression |
| ME-UI-004 | `UNKNOWN` | Windows and macOS target-host geometry, native audio, provider, and accessibility behavior | Run the full target-host matrix and retain screenshots plus logs |
| ME-UI-005 | `PARTIALLY VERIFIED` | Hosted model identity is bound to provider/model/version/time rather than immutable weights | Adopt a provider-supported immutable model identifier when available |

These entries keep future validation actionable. They do not replace the
implemented native UI, passing full regression, or passing deterministic soak.
