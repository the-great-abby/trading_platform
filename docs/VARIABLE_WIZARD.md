# Variable Wizard

The Variable Wizard is an interactive tool that walks you through providing values for Makefile variables before executing targets. It automatically detects which variables are required, missing, or have defaults, and prompts you for values as needed.

## Features

- **Automatic Variable Detection**: Parses Makefiles to identify variables used by each target
- **Smart Status Classification**: Categorizes variables as:
  - ❌ **Missing** - Required variables that must be set
  - ⚠️  **Empty** - Variables with empty defaults that should be set
  - ✅ **Defaults** - Variables with default values (shown for reference)
- **Interactive Prompts**: Friendly prompts with descriptions and current values
- **Integrated with Wizard**: Automatically runs when executing commands through `make wizard`
- **Standalone Usage**: Can be used directly from the command line

## Usage

### Through the Main Wizard

The variable wizard is automatically integrated with the main wizard. When you select a target that requires variables:

1. Run `make wizard` or `make wiz`
2. Navigate to a category and select a command
3. If the target requires variables, you'll see a status summary
4. You'll be prompted to provide values for missing/empty variables
5. The command executes with your provided values

### Standalone Usage

You can also use the variable wizard directly:

```bash
# Show variable status without prompting (use venv Python)
.venv/bin/python scripts/variable_wizard.py <makefile> <target> --no-interactive

# Interactive mode (prompt for variables but don't execute)
.venv/bin/python scripts/variable_wizard.py <makefile> <target> --skip-execution

# Full interactive mode (prompt and execute)
.venv/bin/python scripts/variable_wizard.py <makefile> <target>
```

### Examples

```bash
# Check variables for the 'mark' target
.venv/bin/python scripts/variable_wizard.py makefiles/Makefile.zero-dte mark --no-interactive

# Interactive prompt for variables (then execute)
.venv/bin/python scripts/variable_wizard.py makefiles/Makefile.zero-dte mark
```

## How It Works

1. **Parsing**: The `makefile_parser.py` module parses Makefiles to:
   - Extract variable definitions (with `:=`, `=`, or `?=`)
   - Identify variables referenced in target recipes
   - Determine which variables are required vs optional

2. **Status Checking**: For each variable, the wizard checks:
   - If it's set in the environment (highest priority)
   - If it has a default value in the Makefile
   - If it's missing/required

3. **Interactive Prompting**: The `variable_wizard.py` module:
   - Displays a status summary
   - Prompts for missing/empty variables
   - Shows default values and descriptions
   - Builds the final make command with provided variables

4. **Execution**: The command is executed with all variables properly set

## Variable Assignment Types

The parser recognizes different Makefile variable assignment types:

- `VAR := value` - Immediate assignment (has value, not user-overridable via ?=)
- `VAR = value` - Recursive assignment (has value)
- `VAR ?= value` - Conditional assignment (default if not set)
- `VAR ?=` - Conditional assignment with empty default (user should set)

## Integration with Wizard

The variable wizard is automatically enabled when using `make wizard`. If you want to disable it or if there are issues, the wizard falls back to direct command execution.

## Troubleshooting

- **Parser errors**: If parsing fails, the wizard falls back to direct execution
- **Import errors**: Make sure both `makefile_parser.py` and `variable_wizard.py` are in the `scripts/` directory
- **Variable not detected**: Some complex variable expansions might not be detected; the wizard will still work but may not prompt for all variables

## Technical Details

- **Parser**: Uses regex to parse Makefile syntax (handles `$(VAR)` and `${VAR}` references)
- **Environment**: Checks `os.environ` for current variable values
- **Command Building**: Constructs make commands with `VAR=value` arguments
- **Error Handling**: Gracefully falls back if parsing fails

