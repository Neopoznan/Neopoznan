# Telegram keyword autoresponder

Скрипт логинится в Telegram под вашим личным аккаунтом (через официальный
Telegram API, библиотека [Telethon](https://docs.telethon.dev/)) и следит за
сообщениями в заданной группе. Когда кто-то из других участников пишет
сообщение с одним из ключевых слов, скрипт отправляет в чат обычное новое
сообщение от вашего имени (по умолчанию — «я поеду»).

Это **не бот-аккаунт**: добавлять в группу ничего не нужно, скрипт работает
через ваш собственный аккаунт, как обычный клиент (Telegram Desktop, Web и т.п.).

## Важно

- Использование автоматизации на обычном (не бот) аккаунте формально не
  приветствуется правилами Telegram. При разумной частоте срабатываний
  (единичные сообщения, не десятки в минуту) риск ограничений минимален, но
  он не нулевой — используйте на свой страх и риск.
- Файл сессии (`*.session`) даёт полный доступ к вашему аккаунту — храните
  его так же аккуратно, как пароль, никогда не коммитьте и не пересылайте.
- `TG_API_ID` / `TG_API_HASH` тоже секретные — не публикуйте их.

## Установка

```bash
cd telegram_autoresponder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Настройка

1. Получите `api_id` и `api_hash` на https://my.telegram.org
   (Login -> API development tools -> создать приложение).
2. Скопируйте `.env.example` в `.env` и заполните `TG_API_ID`, `TG_API_HASH`,
   `TG_PHONE` (номер телефона того аккаунта, от имени которого будут идти
   сообщения). `TG_2FA_PASSWORD` заполните, только если у аккаунта включён
   облачный пароль (двухфакторная аутентификация).
3. Скопируйте `config.example.yaml` в `config.yaml` и укажите:
   - `chat` — группа, которую нужно слушать (`@username`, ссылка-приглашение
     или числовой id);
   - `keywords` — список ключевых слов/фраз;
   - `response_text` — что отправлять (по умолчанию «я поеду»);
   - `cooldown_seconds` — минимальный интервал между двумя отправленными
     ответами, чтобы не отвечать слишком часто подряд;
   - `dry_run: true` — на время проверки, чтобы скрипт только логировал
     совпадения, но ничего не отправлял.

## Запуск

```bash
python3 main.py
```

При первом запуске Telethon запросит код подтверждения, который придёт в
Telegram (и пароль 2FA, если он задан не через `.env`). После успешного входа
создастся файл `userbot_session.session` — при следующих запусках повторный
вход не потребуется.

Проверьте сначала с `dry_run: true`, чтобы убедиться, что ключевые слова
ловятся так, как вы ожидаете, затем выключите `dry_run` для реальной отправки.

## Как заставить работать постоянно

Скрипт должен быть запущен постоянно, чтобы ловить новые сообщения. Проще
всего — держать его в `tmux`/`screen` на сервере или своей машине, либо
оформить как systemd-сервис:

```ini
# /etc/systemd/system/tg-autoresponder.service
[Unit]
Description=Telegram keyword autoresponder
After=network.target

[Service]
WorkingDirectory=/path/to/telegram_autoresponder
ExecStart=/path/to/telegram_autoresponder/venv/bin/python3 main.py
Restart=on-failure
EnvironmentFile=/path/to/telegram_autoresponder/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now tg-autoresponder
```
