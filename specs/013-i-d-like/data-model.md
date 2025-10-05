# Data Model: Kubernetes Secrets Management

## Entities

### Secret Configuration
Represents the mapping between .env variables and Kubernetes secret names.

**Fields**:
- `env_variable_name` (string, required): The .env file variable name (e.g., "POLYGON_API_KEY")
- `k8s_secret_name` (string, required): The Kubernetes secret name (e.g., "polygon-api-key")
- `secret_type` (enum, required): Either "api-key" or "database"
- `namespace` (string, required): Kubernetes namespace (default: "default")
- `validation_rules` (array, optional): Custom validation rules for the secret value

**Validation Rules**:
- env_variable_name must match pattern: `^[A-Z][A-Z0-9_]*$`
- k8s_secret_name must match pattern: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`
- secret_type must be one of: ["api-key", "database"]
- namespace must be a valid Kubernetes namespace name

**State Transitions**:
- `defined` → `validated` (when .env file contains the variable)
- `validated` → `created` (when kubectl create succeeds)
- `created` → `updated` (when kubectl patch succeeds)
- Any state → `error` (when validation or kubectl operations fail)

### Environment File
Contains the actual secret values that need to be synchronized with Kubernetes.

**Fields**:
- `file_path` (string, required): Path to the .env file
- `variables` (map<string, string>, required): Key-value pairs from the file
- `last_modified` (timestamp, required): When the file was last changed
- `validation_status` (enum, required): "valid", "invalid", "missing"

**Validation Rules**:
- file_path must exist and be readable
- variables must not contain empty values
- variables must match expected naming patterns
- file permissions must be 600 or more restrictive

**State Transitions**:
- `missing` → `loaded` (when file is successfully read)
- `loaded` → `validated` (when all variables pass validation)
- `validated` → `error` (when validation fails)
- Any state → `error` (when file operations fail)

### Makefile Target
Represents the user interface for performing secret management operations.

**Fields**:
- `target_name` (string, required): The Makefile target name (e.g., "secrets-update")
- `description` (string, required): Human-readable description of the target
- `dependencies` (array, optional): Other Makefile targets that must run first
- `validation_required` (boolean, required): Whether .env validation is required
- `next_steps_template` (string, required): Template for post-operation guidance

**Validation Rules**:
- target_name must follow pattern: `secrets-[action]`
- description must be non-empty and descriptive
- dependencies must reference valid Makefile targets
- next_steps_template must include placeholder for dynamic content

**State Transitions**:
- `defined` → `ready` (when all dependencies are met)
- `ready` → `executing` (when target is invoked)
- `executing` → `completed` (when operation succeeds)
- `executing` → `failed` (when operation fails)

## Relationships

### Secret Configuration ↔ Environment File
- **One-to-Many**: One environment file can contain multiple secret configurations
- **Relationship**: Environment file provides values for secret configurations
- **Constraint**: All referenced secret configurations must exist in the environment file

### Makefile Target ↔ Secret Configuration
- **One-to-Many**: One Makefile target can operate on multiple secret configurations
- **Relationship**: Makefile target orchestrates operations on secret configurations
- **Constraint**: Target must handle all referenced secret configurations

### Environment File ↔ Makefile Target
- **Many-to-One**: Multiple Makefile targets can reference the same environment file
- **Relationship**: Environment file provides input data for Makefile target operations
- **Constraint**: Environment file must be validated before any target execution

## Business Rules

1. **Secret Naming Convention**: Environment variables use underscores, Kubernetes secrets use hyphens
2. **Validation Order**: Environment file validation must occur before secret operations
3. **Error Handling**: Any validation failure must prevent secret operations
4. **Audit Trail**: All secret operations must be logged (without exposing values)
5. **Rollback Capability**: Failed operations must not leave partial state changes
6. **Security**: Secret values must never be logged or exposed in error messages

## Data Flow

1. **Input**: Environment file (.env) with secret values
2. **Processing**: 
   - Parse and validate environment file
   - Map environment variables to secret configurations
   - Convert naming conventions (underscore to hyphen)
   - Validate cluster connectivity
3. **Output**: Updated Kubernetes secrets with success/failure status and next steps

## Constraints

1. **File Format**: Environment file must be valid shell environment format
2. **Permissions**: Environment file must have restrictive permissions (600)
3. **Cluster Access**: kubectl must be configured and cluster must be accessible
4. **Namespace**: All operations must be scoped to specified namespace
5. **Validation**: All secret values must pass validation before cluster operations

