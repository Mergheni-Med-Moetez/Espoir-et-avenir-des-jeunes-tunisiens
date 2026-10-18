# Roles Matrix

## Platform Roles and Permissions

| Role | Django Group | Responsibilities | Case Access | State Transitions |
|---|---|---|---|---|
| **Field Operator** | `Field Operator` | Creates intake records, enters initial data, updates own cases | Own cases only | INTAKE → ASSESSMENT |
| **Supervisor** | `Supervisor` | Validates transitions, escalates critical cases, oversees all | All cases | Any valid transition |
| **System Admin** | `System Admin` | Configures system, views audit logs, manages users | All cases | Any valid transition |

## Permission Matrix

| Action | Field Operator | Supervisor | System Admin |
|---|---|---|---|
| Create Case | ✅ | ✅ | ✅ |
| Edit Own Case | ✅ | ✅ | ✅ |
| Edit Any Case | ❌ | ✅ | ✅ |
| View Audit Logs | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ✅ |
| Configure System | ❌ | ❌ | ✅ |
