# ai-engineer-cli

CLI-инструмент для работы с LLM как с инженерным инструментом.

## Goal

Цель проекта — постепенно построить developer assistant: от простого LLM API клиента до CLI-ассистента с prompt templates, логами, tools, RAG, MCP и локальными моделями.

## Setup

Создать виртуальное окружение:

python3 -m venv .venv

Активировать окружение:

source .venv/bin/activate

Установить зависимости:

pip install -r requirements.txt

## Environment variables

Создай файл .env:

OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini

## Run first request

PYTHONPATH=src python -m ai_engineer_cli.cli "Explain what CLI is in simple terms"

## Day 1 result

Первый запрос успешно выполнен.

Example response:

CLI stands for Command Line Interface. It is a way to interact with a computer by typing text commands instead of clicking on icons or buttons.

## Current architecture

Terminal
  ↓
cli.py
  ↓
config.py
  ↓
llm_client.py
  ↓
OpenAI API
  ↓
response