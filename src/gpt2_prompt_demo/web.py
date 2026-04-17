from __future__ import annotations

import argparse
import json
import threading
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .generator import GenerationConfig, LoadedModel, generate_with_config, load_model, pick_device


HTML_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GPT-2 Prompt Studio</title>
    <style>
      :root {
        --bg: #f2efe8;
        --panel: rgba(255, 250, 240, 0.9);
        --panel-strong: rgba(255, 247, 234, 0.98);
        --ink: #1b1b18;
        --muted: #655a4e;
        --accent: #c35c2f;
        --accent-dark: #8e3817;
        --line: rgba(75, 51, 33, 0.16);
        --shadow: 0 20px 50px rgba(77, 46, 24, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(219, 133, 71, 0.18), transparent 32%),
          radial-gradient(circle at bottom right, rgba(154, 173, 106, 0.18), transparent 28%),
          linear-gradient(135deg, #f6f0e4 0%, #ece6db 48%, #e9dfd1 100%);
        font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      }

      .shell {
        width: min(1180px, calc(100% - 32px));
        margin: 32px auto;
        padding: 28px;
        border: 1px solid var(--line);
        border-radius: 28px;
        background: rgba(255, 252, 246, 0.82);
        backdrop-filter: blur(12px);
        box-shadow: var(--shadow);
      }

      .hero {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 20px;
        align-items: start;
        margin-bottom: 24px;
      }

      .hero-copy h1 {
        margin: 0 0 12px;
        font-size: clamp(2.4rem, 4vw, 4.4rem);
        line-height: 0.96;
        letter-spacing: -0.05em;
        font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      }

      .hero-copy p {
        margin: 0;
        max-width: 58ch;
        color: var(--muted);
        font-size: 1.02rem;
      }

      .hero-card {
        padding: 18px 20px;
        border-radius: 22px;
        background: linear-gradient(160deg, rgba(195, 92, 47, 0.95), rgba(104, 48, 23, 0.95));
        color: #fff7ef;
        min-height: 100%;
      }

      .hero-card .eyebrow {
        display: inline-block;
        margin-bottom: 10px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.14);
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .hero-card strong {
        display: block;
        margin-bottom: 8px;
        font-size: 1.1rem;
      }

      .hero-card p {
        margin: 0;
        color: rgba(255, 247, 239, 0.86);
      }

      .layout {
        display: grid;
        grid-template-columns: minmax(320px, 460px) minmax(0, 1fr);
        gap: 20px;
      }

      .panel {
        padding: 22px;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: var(--panel);
      }

      .panel h2 {
        margin: 0 0 14px;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
      }

      .stack {
        display: grid;
        gap: 14px;
      }

      label {
        display: grid;
        gap: 8px;
        font-size: 0.9rem;
        color: var(--muted);
      }

      input,
      textarea {
        width: 100%;
        border: 1px solid rgba(76, 58, 43, 0.18);
        border-radius: 16px;
        background: var(--panel-strong);
        color: var(--ink);
        padding: 14px 16px;
        font: inherit;
        transition: border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease;
      }

      input:focus,
      textarea:focus {
        outline: none;
        border-color: rgba(195, 92, 47, 0.6);
        box-shadow: 0 0 0 4px rgba(195, 92, 47, 0.12);
        transform: translateY(-1px);
      }

      textarea {
        min-height: 220px;
        resize: vertical;
      }

      .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }

      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 13px 18px;
        font: inherit;
        cursor: pointer;
        transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
      }

      button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(66, 33, 18, 0.14);
      }

      button:disabled {
        cursor: wait;
        opacity: 0.7;
        transform: none;
        box-shadow: none;
      }

      .primary {
        background: linear-gradient(135deg, var(--accent), var(--accent-dark));
        color: #fff8f2;
      }

      .ghost {
        background: rgba(101, 90, 78, 0.08);
        color: var(--ink);
      }

      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .chip {
        background: rgba(195, 92, 47, 0.08);
        color: var(--accent-dark);
        border: 1px solid rgba(195, 92, 47, 0.14);
      }

      .status {
        margin-top: 16px;
        padding: 14px 16px;
        border-radius: 18px;
        background: rgba(93, 80, 66, 0.08);
        color: var(--muted);
        min-height: 52px;
      }

      .result-box {
        min-height: 520px;
        padding: 24px;
        border-radius: 22px;
        background:
          linear-gradient(180deg, rgba(255, 252, 245, 0.96), rgba(246, 239, 229, 0.96));
        border: 1px solid rgba(86, 62, 42, 0.14);
      }

      .result-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: center;
        margin-bottom: 16px;
      }

      .result-head strong {
        font-size: 1.15rem;
      }

      .meta {
        color: var(--muted);
        font-size: 0.9rem;
      }

      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.7;
        font-family: "SFMono-Regular", "JetBrains Mono", "Menlo", monospace;
        font-size: 0.96rem;
      }

      .empty {
        color: var(--muted);
        font-style: italic;
      }

      @media (max-width: 940px) {
        .hero,
        .layout {
          grid-template-columns: 1fr;
        }

        .shell {
          width: min(100% - 20px, 1180px);
          margin: 10px auto 20px;
          padding: 18px;
        }

        .grid-2,
        .grid-3 {
          grid-template-columns: 1fr;
        }

        .result-box {
          min-height: 360px;
        }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div class="hero-copy">
          <h1>GPT-2 Prompt Studio</h1>
          <p>
            A local browser UI for trying prompts, tweaking sampling controls,
            and swapping GPT-2 style models without leaving your machine.
          </p>
        </div>
        <aside class="hero-card">
          <span class="eyebrow">Local Runtime</span>
          <strong>Model stays in your Python process</strong>
          <p>
            The first request may take longer while the model downloads. After that,
            generation reuses the loaded model until you switch to another one.
          </p>
        </aside>
      </section>

      <section class="layout">
        <div class="panel">
          <h2>Controls</h2>
          <form id="generator-form" class="stack">
            <label>
              Prompt
              <textarea id="prompt" name="prompt" placeholder="Write a prompt here...">Once upon a time in a city of brass,</textarea>
            </label>

            <label>
              Model
              <input id="model" name="model" value="gpt2" />
            </label>

            <div class="grid-2">
              <label>
                Max New Tokens
                <input id="max_new_tokens" name="max_new_tokens" type="number" min="1" max="512" value="80" />
              </label>
              <label>
                Seed
                <input id="seed" name="seed" type="number" value="42" />
              </label>
            </div>

            <div class="grid-3">
              <label>
                Temperature
                <input id="temperature" name="temperature" type="number" min="0.1" max="2.0" step="0.1" value="0.9" />
              </label>
              <label>
                Top-K
                <input id="top_k" name="top_k" type="number" min="1" max="200" value="50" />
              </label>
              <label>
                Top-P
                <input id="top_p" name="top_p" type="number" min="0.1" max="1.0" step="0.01" value="0.95" />
              </label>
            </div>

            <div class="actions">
              <button class="primary" id="generate-btn" type="submit">Generate</button>
              <button class="ghost" id="clear-btn" type="button">Clear Output</button>
            </div>

            <div class="chips">
              <button class="chip" type="button" data-example="Write a cyberpunk detective opening scene set in Shanghai.">Cyberpunk</button>
              <button class="chip" type="button" data-example="从前有一座山，山上有一座道观，">Chinese Prompt</button>
              <button class="chip" type="button" data-example="The future of open source AI depends on">Open Source</button>
            </div>
          </form>

          <div class="status" id="status">Ready. Enter a prompt and hit Generate.</div>
        </div>

        <div class="panel result-box">
          <div class="result-head">
            <strong>Generated Text</strong>
            <span class="meta" id="meta">Model: gpt2</span>
          </div>
          <pre id="output" class="empty">Your generation will appear here.</pre>
        </div>
      </section>
    </main>

    <script>
      const form = document.getElementById("generator-form");
      const output = document.getElementById("output");
      const statusBox = document.getElementById("status");
      const meta = document.getElementById("meta");
      const generateBtn = document.getElementById("generate-btn");
      const clearBtn = document.getElementById("clear-btn");
      const promptInput = document.getElementById("prompt");
      const modelInput = document.getElementById("model");

      function setStatus(message) {
        statusBox.textContent = message;
      }

      function renderEmpty() {
        output.textContent = "Your generation will appear here.";
        output.classList.add("empty");
      }

      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
          prompt: promptInput.value,
          model: modelInput.value,
          max_new_tokens: Number(document.getElementById("max_new_tokens").value),
          temperature: Number(document.getElementById("temperature").value),
          top_k: Number(document.getElementById("top_k").value),
          top_p: Number(document.getElementById("top_p").value),
          seed: Number(document.getElementById("seed").value),
        };

        generateBtn.disabled = true;
        setStatus("Generating... the first request can take longer if the model is still downloading.");

        try {
          const response = await fetch("/api/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload),
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Generation failed.");
          }

          output.textContent = data.generated_text;
          output.classList.remove("empty");
          meta.textContent = `Model: ${data.model} | Device: ${data.device}`;
          setStatus("Done. You can edit the prompt or tweak parameters and run again.");
        } catch (error) {
          output.textContent = error.message;
          output.classList.remove("empty");
          meta.textContent = "Generation failed";
          setStatus("Something went wrong. Check the message on the right and try again.");
        } finally {
          generateBtn.disabled = false;
        }
      });

      clearBtn.addEventListener("click", () => {
        renderEmpty();
        meta.textContent = `Model: ${modelInput.value || "gpt2"}`;
        setStatus("Output cleared.");
      });

      document.querySelectorAll("[data-example]").forEach((button) => {
        button.addEventListener("click", () => {
          promptInput.value = button.dataset.example;
          promptInput.focus();
          setStatus("Example prompt loaded. Adjust it however you like.");
        });
      });
    </script>
  </body>
</html>
"""


class ModelManager:
    def __init__(self, device: str, default_model: str, cache_dir: str | None = None):
        self.device = device
        self.cache_dir = cache_dir
        self.current_model_name: str | None = None
        self.runtime: LoadedModel | None = None
        self.lock = threading.Lock()
        self.ensure_model(default_model)

    def ensure_model(self, model_name: str) -> LoadedModel:
        with self.lock:
            if self.runtime is not None and self.current_model_name == model_name:
                return self.runtime

            runtime = load_model(model_name=model_name, device=self.device, cache_dir=self.cache_dir)
            self.runtime = runtime
            self.current_model_name = model_name
            return runtime

    def generate(self, model_name: str, prompt: str, config: GenerationConfig) -> dict[str, str]:
        with self.lock:
            if self.runtime is None or self.current_model_name != model_name:
                self.runtime = load_model(model_name=model_name, device=self.device, cache_dir=self.cache_dir)
                self.current_model_name = model_name

            generated_text = generate_with_config(self.runtime, prompt, config)

        return {
            "model": model_name,
            "device": self.device,
            "generated_text": generated_text,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the GPT-2 local web demo.")
    parser.add_argument("--model", default="gpt2", help="Default model to preload.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the local server.")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Which device to use.",
    )
    parser.add_argument("--cache-dir", help="Optional Hugging Face cache directory.")
    return parser


def parse_request_payload(raw_body: bytes) -> tuple[str, str, GenerationConfig]:
    payload = json.loads(raw_body.decode("utf-8"))

    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    model_name = str(payload.get("model", "gpt2")).strip() or "gpt2"
    config = GenerationConfig(
        max_new_tokens=int(payload.get("max_new_tokens", 80)),
        temperature=float(payload.get("temperature", 0.9)),
        top_k=int(payload.get("top_k", 50)),
        top_p=float(payload.get("top_p", 0.95)),
        seed=int(payload.get("seed", 42)),
    )
    return prompt, model_name, config


def make_handler(model_manager: ModelManager):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:
            if self.path != "/":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            self._send_html(HTML_PAGE)

        def do_POST(self) -> None:
            if self.path != "/api/generate":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)

            try:
                prompt, model_name, config = parse_request_payload(raw_body)
                result = model_manager.generate(model_name=model_name, prompt=prompt, config=config)
                result["config"] = asdict(config)
                self._send_json(result)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args) -> None:
            return

    return Handler


def main() -> None:
    args = build_parser().parse_args()
    device = pick_device(args.device)

    print(f"Loading default model '{args.model}' on device '{device}'...")
    model_manager = ModelManager(device=device, default_model=args.model, cache_dir=args.cache_dir)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(model_manager))

    print(f"Web UI ready at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
