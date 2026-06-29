To run, do

```bash
kill $(lsof -ti tcp:8765); uv run python scripts/run_interactive.py
```


```bash
/Users/zhanwenchen/llama.cpp/build/bin/llama-server \
  -m /Users/zhanwenchen/sqmem/qwen3.5_9b/Qwen3.5-9B-UD-Q4_K_XL.gguf \
  --port 8080 \
  --ctx-size 8192 \
  -ngl 999 \
  --api-key local \
  --jinja \
  --chat-template-kwargs '{"enable_thinking":false}'
```


```bash
cd /Users/zhanwenchen/personalgui
python scripts/run_pilot.py \
  --tasks all \
  --agents "" \
  --llm \
  --llm-base-url http://localhost:8080/v1 \
  --llm-model qwen3.5-9b \
  --llm-api-key local \
  --llm-max-messages 24
```
