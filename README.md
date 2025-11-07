# GitHub Release Monitor

A Python application that monitors GitHub repository releases and sends notifications through webhooks when new releases
are detected.

## Features

- Monitors multiple GitHub repositories for new releases
- Skips draft releases (configurable)
- Supports custom webhook notifications with templated messages
- Maintains state between runs
- Timezone-aware notifications
- GitHub Actions integration for automated monitoring

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   uv python install
   uv sync --locked --all-extras --dev
   ```
3. Run main.py:
   ```bash
   export WEBHOOK__URL="https://hooks.slack.com/services/..." 
   uv run main.py
   ```

## Configuration

Create a `config.yaml` file with the following structure:

```yaml
# List of GitHub repositories to monitor (required)
repos:
  - owner/repo1
  - owner/repo2

# Path to the state file (optional, default: "state.yaml")
# Used to track the latest releases between runs
state_file: state.yaml

# Whether to skip draft releases (optional, default: true)
skip_draft: true

# Webhook configuration for notifications (optional)
webhook:
  # Webhook URL to send notifications to (required if webhook is specified)
  url: https://hooks.slack.com/services/...

  # Content template for the notification (optional)
  # Supports the following variables:
  # - ${repo_name}: Repository name (e.g., "owner/repo")
  # - ${id}: Release ID
  # - ${html_url}: URL to the release page
  # - ${tag_name}: Release tag name
  # - ${name}: Release name
  # - ${published_at}: Release publication date in ISO format
  # - ${body}: Release description
  content: |
    {
      "text": "New release: ${repo_name} ${tag_name}"
    }

  # Additional data to send with the webhook (optional)
  data:
    key: value

  # HTTP headers for the webhook request (optional)
  headers:
    Content-Type: application/json

# Timezone for date/time formatting (optional, default: "UTC")
# Uses IANA timezone database names (e.g., "America/New_York", "Europe/London")
timezone: UTC

# Logging level (optional, default: "INFO")
# Possible values: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
log_level: INFO
```

### Configuration Details

#### Required Fields

- `repos`: A list of GitHub repositories to monitor in the format `owner/repo`.

#### Optional Fields

- `state_file`: Path to the file used to store the state between runs. Default: `state.yaml`.
- `skip_draft`: Whether to skip draft releases. Default: `true`.
- `webhook`: Configuration for sending notifications when new releases are detected.
  - `url`: The webhook URL to send notifications to (required if webhook is specified).
  - `content`: A template string for the notification content. Supports variable substitution.
  - `data`: Additional data to send with the webhook request.
  - `headers`: HTTP headers for the webhook request.
- `timezone`: The timezone to use for date/time formatting. Default: `UTC`.
- `log_level`: The logging level. Default: `INFO`.

#### Template Variables

When using the `webhook.content` template, the following variables are available:

- `${repo_name}`: Repository name (e.g., "owner/repo")
- `${id}`: Release ID
- `${html_url}`: URL to the release page
- `${tag_name}`: Release tag name
- `${name}`: Release name
- `${published_at}`: Release publication date in ISO format with timezone
- `${body}`: Release description
