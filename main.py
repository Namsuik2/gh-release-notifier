import json
import logging
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

import httpx
import yaml
from github import Github
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    NoDecode,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

log = logging.getLogger(__name__)


class Webhook(BaseModel):
    url: str
    content: str | None = None
    data: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_implicit_flags=True,
        env_nested_delimiter="__",
        yaml_file=["config.yaml", "config.yml"],
        yaml_file_encoding="utf-8",
    )

    repos: Annotated[list[str], NoDecode]
    state_file: Path = "state.yaml"
    skip_draft: bool = True
    webhook: Webhook | None = None
    timezone: str = "UTC"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )


class State(BaseModel):
    id: int
    html_url: str
    tag_name: str
    name: str
    published_at: datetime


class StateFile(BaseModel):
    states: dict[str, State]


def escape(s: str) -> str:
    o = json.dumps(s, ensure_ascii=False, allow_nan=False)
    return o[1:-1]


def main():
    cfg = Settings()

    # Setup logging
    logging.basicConfig(level=cfg.log_level)

    # Initialize timezone
    tz = ZoneInfo(cfg.timezone)

    # Initialize GitHub API
    g = Github()

    # Load state file
    if cfg.state_file.is_file():
        with cfg.state_file.open("r", encoding="utf-8") as f:
            obj = yaml.safe_load(f)
        state_file = StateFile(**obj)
    else:
        state_file = StateFile(states={})

    for repo_name in cfg.repos:
        repo = g.get_repo(repo_name, lazy=True)
        release = repo.get_latest_release()

        if cfg.skip_draft and release.draft:
            continue

        # Get previous state if any
        prev_state = state_file.states.get(repo_name)

        # Update state
        state_file.states[repo_name] = State(
            id=release.id,
            html_url=release.html_url,
            tag_name=release.tag_name,
            name=release.name or release.tag_name,
            published_at=release.published_at,
        )

        if prev_state and prev_state.published_at >= release.published_at:
            log.info(f"{repo_name}: No new release")
            continue

        log.info(
            f"{repo_name}: "
            f"New release: {release.name or release.tag_name} / {release.tag_name} / {release.published_at.isoformat()}"
        )

        # Send notification
        if not cfg.webhook:
            continue

        content = cfg.webhook.content

        if content:
            s = Template(content)
            content = s.safe_substitute(
                repo_name=repo_name,
                id=release.id,
                html_url=release.html_url,
                tag_name=release.tag_name,
                name=escape(release.name or release.tag_name),
                published_at=release.published_at.astimezone(tz).isoformat(),
                body=escape(release.body or ""),
            )

        try:
            r = httpx.post(
                cfg.webhook.url,
                content=content,
                data=cfg.webhook.data,
                headers=cfg.webhook.headers,
                follow_redirects=True,
            )
            r.raise_for_status()
            log.debug(f"{repo_name}: Notification sent")
        except Exception as e:
            log.error(f"{repo_name}: Failed to send notification: {e}")

    # Dump state file
    obj = state_file.model_dump()
    with cfg.state_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, default_flow_style=False, explicit_start=True)


if __name__ == "__main__":
    main()
