# Telegram Channel Summarizer Bot

This bot aggregates content from specified Telegram channels and provides summaries using the LLAMA language model.

## Features

- Add/remove Telegram channels to monitor
- List monitored channels
- Generate summaries of channel content
- Uses LLAMA model for text summarization
- Caches summaries for 24 hours

## Setup

1. Create a new bot on Telegram using [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Create a `.env` file and add your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ```
4. Install dependencies:
   ```
   npm install
   ```
5. Start the bot:
   ```
   npm run dev
   ```

## Commands

- `/start` - Initialize the bot
- `/add_channel <channel_link>` - Add a channel to monitor
- `/list_channels` - List all monitored channels
- `/remove_channel <channel_link>` - Remove a channel
- `/get_summary` - Get today's summary of all channels

## Technical Details

- Built with Grammy (Telegram Bot Framework)
- Uses @xenova/transformers for LLAMA model integration
- Implements caching using node-cache
- Written in TypeScript