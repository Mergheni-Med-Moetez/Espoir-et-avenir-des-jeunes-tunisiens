# State Machine

## Case Workflow States

```
┌─────────┐      ┌────────────┐      ┌────────┐      ┌──────────┐      ┌────────┐
│  INTAKE  │ ──→  │ ASSESSMENT │ ──→  │ ACTIVE │ ──→  │ FOLLOWUP │ ──→  │ CLOSED │
└─────────┘      └────────────┘      └────────┘      └──────────┘      └────────┘
                       │  ↑               │  ↑              │  ↑
                       │  │               │  │              │  │
                       ↓  │               ↓  │              ↓  │
                   ┌─────────┐       ┌────────────┐    ┌────────┐
                   │  INTAKE  │       │ ASSESSMENT │    │ ACTIVE │
                   │ (return) │       │  (re-eval) │    │(reopen)│
                   └─────────┘       └────────────┘    └────────┘
```

## Transition Rules

| From State | Allowed Next States | Reason |
|---|---|---|
| **INTAKE** | ASSESSMENT | Initial data collected, ready for supervisor review |
| **ASSESSMENT** | ACTIVE, INTAKE | Supervisor approves intervention, or returns for more info |
| **ACTIVE** | FOLLOWUP, ASSESSMENT | Intervention complete, or needs re-assessment |
| **FOLLOWUP** | CLOSED, ACTIVE | Case resolved, or needs further intervention |
| **CLOSED** | *(none — terminal)* | Case is fully resolved, no further transitions |

## Blocked Transitions (with reasons)

| Blocked Path | Why It's Blocked |
|---|---|
| INTAKE → ACTIVE | Cannot skip assessment — supervisor must evaluate first |
| INTAKE → FOLLOWUP | Cannot skip assessment and intervention |
| INTAKE → CLOSED | Cannot close without any assessment or intervention |
| ASSESSMENT → FOLLOWUP | Cannot skip the active intervention phase |
| ASSESSMENT → CLOSED | Cannot close during assessment |
| ACTIVE → INTAKE | Cannot return to intake from active intervention |
| ACTIVE → CLOSED | Cannot close without follow-up verification |
| FOLLOWUP → INTAKE | Cannot return to intake from follow-up |
| FOLLOWUP → ASSESSMENT | Cannot return to assessment from follow-up |
| CLOSED → *(anything)* | Terminal state — prevents accidental reopening |

## Implementation

The state machine is implemented as a Python dictionary on the `Case` model:

```python
ALLOWED_TRANSITIONS = {
    Status.INTAKE:     [Status.ASSESSMENT],
    Status.ASSESSMENT: [Status.ACTIVE, Status.INTAKE],
    Status.ACTIVE:     [Status.FOLLOWUP, Status.ASSESSMENT],
    Status.FOLLOWUP:   [Status.CLOSED, Status.ACTIVE],
    Status.CLOSED:     [],
}
```

Transitions are enforced by the `Case.transition_to(new_status, actor)` method,
which raises `ValidationError` if the transition is not in `ALLOWED_TRANSITIONS`.
