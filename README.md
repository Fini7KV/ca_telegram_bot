# CA Telegram Bot — Render-ready (FastAPI + webhook)

This project contains a webhook-driven Telegram bot designed for CA Foundation study queries using the OpenAI API (Chat Completions). It is optimized for stability and quick replies using background tasks.

## What you'll get
- `main.py` — FastAPI app that handles Telegram webhook, commands, and OpenAI calls in background.
- `questions.json` — sample MTP/RTP/PYQ DB (edit to add your content).
- `set_webhook.py` — helper to set Telegram webhook after deployment.
- `render.yaml` — Render service definition (optional if you prefer web UI).
- `requirements.txt`, `.env.example`, `Dockerfile`, `Procfile` and README.

## How it works (short)
1. Deploy this repo to Render (or any host) as a web service.
2. Set environment variables TELEGRAM_TOKEN and OPENAI_KEY (and PUBLIC_URL used for the helper).
3. Run `python set_webhook.py` (or call the Telegram API manually) to configure webhook.
4. Ask commands in Telegram: `/mtp`, `/rtp`, `/pyq`, `/test 5`, `/ask <question>` or just type a question.

## Deployment on Render (recommended)
1. Create a new Web Service on Render.
2. Link your GitHub repo (or drag the zip as a repo). For quick upload you can create a new Private GitHub repo and push the code, or use Render's manual deploy with a zip.
3. Use Python environment. Build command is `pip install -r requirements.txt`. Start command is `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Add environment variables in Render dashboard:
   - `TELEGRAM_TOKEN` = your Telegram token (keep secret)
   - `OPENAI_KEY` = your OpenAI API key (keep secret)
   - `PUBLIC_URL` = the URL of your Render service (e.g. https://ca-telegram-bot.onrender.com)
   - (optional) `WEBHOOK_SECRET_PATH` = an extra path segment to make webhook URL secret (e.g. 's3cr3t')
5. After deploy, open Shell/Console on Render and run:
   ```bash
   python set_webhook.py
   ```
   This will call Telegram's `setWebhook` API and point Telegram updates to your Render URL.
6. Your bot should now receive messages & reply using OpenAI.

## Security and scaling notes
- Do not share `TELEGRAM_TOKEN` or `OPENAI_KEY` publicly.
- For many users and production use, switch from the JSON file DB to Postgres or MongoDB and add rate-limiting & caching.
- Consider a paid OpenAI plan or batching approach for heavy usage to avoid hitting rate limits.
- Use `max_connections` (set in setWebhook) and use background tasks (done here) to keep the webhook responsive.

## Need help?
If you want, I can:
- Convert DB to Postgres and add admin UI to upload MTP/RTP/PYQ.
- Deploy to Render step-by-step using screenshots.
- Add usage analytics and basic auth for admin endpoints.
