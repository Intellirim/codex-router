# codex-router

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Intelligent routing and orchestration for multi-model AI coding agents**

`codex-router` is a lightweight CLI tool that automatically routes coding tasks to the best available AI model (Claude, GPT, Gemini, or local) based on task complexity, cost, and availability. Manage parallel agent sessions, track token usage and costs across providers, and get unified output streaming. Makes it trivial to leverage multiple AI models without manual context switching.

## Features

- **Smart routing**: Analyzes task complexity and routes to optimal model (fast models for simple tasks, frontier models for complex ones)
- **Parallel orchestration**: Run multiple AI agents on different subtasks simultaneously with unified output
- **Cost tracking**: Real-time token usage and cost monitoring across all providers (Claude, OpenAI, Gemini)
- **Auto-fallback**: Automatically switches to alternative model if primary hits rate limits or errors
- **Unified config**: Single configuration file for all API keys and preferences
- **Session management**: Save and resume multi-agent sessions with full context
- **ASCII-only output**: Cross-platform terminal compatibility (Windows, macOS, Linux)

## Installation

Install via pip:

```bash
pip install codex-router
```

## Quick Start

Configure your API keys:

```bash
codex-router config --set anthropic_api_key YOUR_CLAUDE_KEY
codex-router config --set openai_api_key YOUR_OPENAI_KEY
codex-router config --set google_api_key YOUR_GEMINI_KEY
```

Set default preferences:

```bash
codex-router config --set-default-model claude
```

## Usage Examples

Run a single coding task with intelligent model selection:

```bash
codex-router task "refactor auth module"
```

Output:
```
[Router] Analyzing task complexity...
[Router] Task complexity: HIGH -> Selected model: claude-opus-4
[Agent-1] Reading auth module...
[Agent-1] Identified 3 refactoring opportunities
[Agent-1] Applying changes...
[Agent-1] DONE - 2,450 tokens used ($0.073)
```

Run parallel agents on multiple subtasks:

```bash
codex-router task "add unit tests" --parallel 2
```

Output:
```
[Router] Splitting task into 2 parallel agents
[Agent-1] Testing user authentication flow...
[Agent-2] Testing database connections...
[Agent-1] Created 5 test cases
[Agent-2] Created 3 test cases
[Router] DONE - Total: 3,120 tokens ($0.094)
```

Constrain budget for cost control:

```bash
codex-router task "add unit tests" --model claude --budget 0.50
```

Check usage statistics:

```bash
codex-router status --show-costs
```

Output:
```
Token Usage Summary (Last 7 Days)
---------------------------------
Provider    | Tokens  | Cost
---------------------------------
Claude      | 45,230  | $1.35
OpenAI      | 12,500  | $0.25
Gemini      | 8,900   | $0.00
---------------------------------
Total                 | $1.60
```

## Configuration

Configuration is stored in `~/.codex-router/config.yaml`. You can edit it manually or use the CLI:

```bash
# Set API keys
codex-router config --set anthropic_api_key YOUR_KEY
codex-router config --set openai_api_key YOUR_KEY
codex-router config --set google_api_key YOUR_KEY

# Set default model
codex-router config --set-default-model gpt-4

# Set budget limits
codex-router config --set daily_budget 5.00
```

## How It Works

1. **Task Analysis**: The router analyzes your task description for complexity, required context, and estimated token usage
2. **Model Selection**: Based on complexity and your preferences, selects the optimal model (e.g., GPT-3.5 for simple tasks, Claude Opus for complex refactoring)
3. **Execution**: Sends the task to the selected provider's API with proper context and streaming
4. **Cost Tracking**: Records token usage and costs in a local database for monitoring
5. **Auto-Fallback**: If the primary model fails (rate limit, timeout), automatically retries with an alternative model

## Development

Clone the repository:

```bash
git clone https://github.com/Intellirim/codex-router.git
cd codex-router
```

Install in development mode:

```bash
pip install -e .
```

Run tests:

```bash
pytest tests/
```

## License

MIT License - Copyright (c) 2026 Intellirim

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
