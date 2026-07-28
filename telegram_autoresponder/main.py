"""
Userbot-автоответчик для Telegram.

Логинится под личным аккаунтом пользователя (не бот-аккаунт, поэтому его не
нужно и нельзя добавлять в чужой канал/группу отдельно) и следит за
сообщениями в указанном чате. Когда кто-то из других участников пишет
сообщение, содержащее одно из ключевых слов, скрипт отправляет в чат
обычное новое сообщение от имени пользователя.

Настройка: скопировать .env.example -> .env и config.example.yaml ->
config.yaml, заполнить своими значениями. Подробности в README.md.
"""

import asyncio
import logging
import os
import re
import time

import yaml
from dotenv import load_dotenv
from telethon import TelegramClient, events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("autoresponder")

CONFIG_PATH = os.environ.get("AUTORESPONDER_CONFIG", "config.yaml")
SESSION_NAME = os.environ.get("AUTORESPONDER_SESSION", "userbot_session")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    required = ["chat", "keywords", "response_text"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError(f"В конфиге {path} не заданы обязательные поля: {missing}")

    config.setdefault("cooldown_seconds", 60)
    config.setdefault("dry_run", False)
    return config


def compile_keyword_patterns(keywords: list[str]) -> list[re.Pattern]:
    patterns = []
    for keyword in keywords:
        escaped = re.escape(keyword.strip())
        # \s+ вместо буквального пробела, чтобы "кто едет" совпадало и при
        # двойном пробеле/переносе строки между словами.
        escaped = escaped.replace(r"\ ", r"\s+")
        patterns.append(re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE | re.UNICODE))
    return patterns


def find_matched_keyword(text: str, keywords: list[str], patterns: list[re.Pattern]) -> str | None:
    if not text:
        return None
    for keyword, pattern in zip(keywords, patterns):
        if pattern.search(text):
            return keyword
    return None


async def main() -> None:
    load_dotenv()

    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    phone = os.environ.get("TG_PHONE")
    password = os.environ.get("TG_2FA_PASSWORD") or None

    if not api_id or not api_hash or not phone:
        raise SystemExit(
            "Не заданы TG_API_ID / TG_API_HASH / TG_PHONE. "
            "Скопируйте .env.example в .env и заполните значения."
        )

    config = load_config(CONFIG_PATH)
    keywords = config["keywords"]
    patterns = compile_keyword_patterns(keywords)
    chat = config["chat"]
    response_text = config["response_text"]
    cooldown_seconds = config["cooldown_seconds"]
    dry_run = config["dry_run"]

    last_sent_at = 0.0

    client = TelegramClient(SESSION_NAME, int(api_id), api_hash)

    @client.on(events.NewMessage(chats=chat))
    async def handler(event: events.NewMessage.Event) -> None:
        nonlocal last_sent_at

        # Не реагируем на собственные сообщения, включая ответ бота.
        if event.out:
            return

        text = event.raw_text or ""
        matched = find_matched_keyword(text, keywords, patterns)
        if not matched:
            return

        sender = await event.get_sender()
        sender_name = getattr(sender, "username", None) or getattr(sender, "first_name", "unknown")

        now = time.monotonic()
        elapsed = now - last_sent_at
        if elapsed < cooldown_seconds:
            log.info(
                "Совпадение %r от %s проигнорировано: cooldown ещё %.0f сек.",
                matched,
                sender_name,
                cooldown_seconds - elapsed,
            )
            return

        log.info("Совпадение %r от %s -> отправляю ответ.", matched, sender_name)

        if dry_run:
            log.info("[dry_run] Отправка пропущена, response_text=%r", response_text)
            return

        await client.send_message(chat, response_text)
        last_sent_at = now

    await client.start(phone=phone, password=password)
    me = await client.get_me()
    log.info(
        "Залогинен как %s (id=%s). Слежу за чатом %r, ключевые слова: %s",
        getattr(me, "username", None) or me.first_name,
        me.id,
        chat,
        keywords,
    )
    log.info("Ожидаю сообщения... (Ctrl+C для остановки)")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
