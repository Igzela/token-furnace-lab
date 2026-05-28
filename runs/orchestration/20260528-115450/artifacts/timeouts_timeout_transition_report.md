# Timeout Transition Semantics Report

Timeout transitions found: 11

| Event | Target |
|-------|--------|
| timeout_5s | CONTROLLED_DECEL |
| timeout_500ms_2s | OPEN_LOOP_RECOVERY |
| timeout_3s | RESTART_PENDING |
| timeout_5s | PASSIVE_COAST |
| timeout_3s | FAULT_LATCHED |
| timeout_5s | FAULT_LATCHED |
| timeout_500ms | FAULT_LATCHED |
| timeout_200ms | RESTART_PENDING |
| timeout_500ms | RESTART_PENDING |
| timeout_200ms | PASSIVE_COAST |
| timeout_100ms | PASSIVE_COAST |

## Unsafe direct transitions: 6
- timeout_3s → RESTART_PENDING (should route through PASSIVE_COAST)
- timeout_3s → FAULT_LATCHED (should route through PASSIVE_COAST)
- timeout_5s → FAULT_LATCHED (should route through PASSIVE_COAST)
- timeout_500ms → FAULT_LATCHED (should route through PASSIVE_COAST)
- timeout_200ms → RESTART_PENDING (should route through PASSIVE_COAST)
- timeout_500ms → RESTART_PENDING (should route through PASSIVE_COAST)
