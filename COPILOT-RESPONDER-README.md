# Copilot responder automation

This branch adds a minimal GitHub Action that responds to comments mentioning `@copilot` by calling an LLM and posting the generated reply back to the issue or PR.

How it works
- The workflow .github/workflows/copilot-respond.yml runs on new issue comments.
- If the comment body contains the literal `@copilot`, the Action runs .github/scripts/respond.js.
- The script sends the comment text to an LLM (OpenAI in this example) and posts the generated reply as a new issue/PR comment.
- Each generated reply is prefixed with the line `Copilot Response:` for provenance.

Secrets
- OPENAI_API_KEY: required. Add this to repository Secrets with a key that can call your chosen LLM.
- (Optional) BOT_TOKEN: a machine user Personal Access Token (repo scope). If present, the Action will post replies as that account. If omitted, replies are posted by the GitHub Actions bot (github-actions[bot]).

Safety notes
- The script ignores comments authored by common bot accounts to avoid loops. You may want to extend this allow/deny list.
- Only trigger on an explicit mention `@copilot` to reduce accidental runs.

Usage
1. Add the OPENAI_API_KEY secret (and BOT_TOKEN if you want a distinct identity).
2. Merge the PR and the Action will be active. When you comment `@copilot` in a PR or issue, the Action will reply.
