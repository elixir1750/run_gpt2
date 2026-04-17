from __future__ import annotations

import argparse
from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed


@dataclass
class LoadedModel:
    model: AutoModelForCausalLM
    tokenizer: AutoTokenizer
    device: str


@dataclass
class GenerationConfig:
    max_new_tokens: int = 80
    temperature: float = 0.9
    top_k: int = 50
    top_p: float = 0.95
    seed: int | None = None


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested

    if torch.cuda.is_available():
        return "cuda"

    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend and torch.backends.mps.is_available():
        return "mps"

    return "cpu"


def load_model(model_name: str, device: str, cache_dir: str | None = None) -> LoadedModel:
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=cache_dir)
    model.to(device)
    model.eval()

    return LoadedModel(model=model, tokenizer=tokenizer, device=device)


def generate_once(
    runtime: LoadedModel,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    top_p: float,
) -> str:
    return generate_with_config(
        runtime=runtime,
        prompt=prompt,
        config=GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        ),
    )


def generate_with_config(runtime: LoadedModel, prompt: str, config: GenerationConfig) -> str:
    if config.seed is not None:
        set_seed(config.seed)

    encoded = runtime.tokenizer(prompt, return_tensors="pt")
    encoded = {name: tensor.to(runtime.device) for name, tensor in encoded.items()}

    with torch.no_grad():
        output_ids = runtime.model.generate(
            **encoded,
            do_sample=True,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_k=config.top_k,
            top_p=config.top_p,
            repetition_penalty=1.1,
            pad_token_id=runtime.tokenizer.eos_token_id,
        )

    return runtime.tokenizer.decode(output_ids[0], skip_special_tokens=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local GPT-2 prompt generation demo.")
    parser.add_argument("--model", default="gpt2", help="Model name or local path.")
    parser.add_argument("--prompt", help="Single prompt to generate from.")
    parser.add_argument("--interactive", action="store_true", help="Run a simple REPL.")
    parser.add_argument("--max-new-tokens", type=int, default=80, help="Number of new tokens to generate.")
    parser.add_argument("--temperature", type=float, default=0.9, help="Sampling temperature.")
    parser.add_argument("--top-k", type=int, default=50, help="Top-k sampling value.")
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling value.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Which device to use.",
    )
    parser.add_argument("--cache-dir", help="Optional Hugging Face cache directory.")
    return parser


def run_interactive(
    runtime: LoadedModel,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    top_p: float,
) -> None:
    print("Interactive mode started. Type a prompt and press Enter.")
    print("Use 'exit', 'quit', or an empty line to stop.\n")

    while True:
        prompt = input("prompt> ").strip()
        if prompt.lower() in {"", "exit", "quit"}:
            print("Bye.")
            return

        generated = generate_once(
            runtime=runtime,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        )
        print("\n=== generated ===")
        print(generated)
        print()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.prompt and not args.interactive:
        parser.error("Please provide --prompt or use --interactive.")

    set_seed(args.seed)
    device = pick_device(args.device)
    print(f"Loading model '{args.model}' on device '{device}'...")
    runtime = load_model(model_name=args.model, device=device, cache_dir=args.cache_dir)

    if args.interactive:
        run_interactive(
            runtime=runtime,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
        )
        return

    generated = generate_once(
        runtime=runtime,
        prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
    )
    print("\n=== generated ===")
    print(generated)
