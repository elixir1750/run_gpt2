# GPT-2 Prompt Demo

一个最小可运行的小仓库，用来在本地给 GPT-2 输入 prompt 并查看生成结果。
现在同时支持命令行和本地网页界面。

## 适合什么场景

- 想快速验证 GPT-2 的续写效果
- 想本地试不同 prompt 的生成表现
- 想把默认模型从 `gpt2` 切到别的 Hugging Face 因果语言模型

## 目录结构

```text
.
├── README.md
├── pyproject.toml
├── requirements.txt
├── run_clm.py
└── src/
    └── gpt2_prompt_demo/
        ├── __init__.py
        ├── __main__.py
        ├── generator.py
        └── web.py
```

`run_clm.py` 是已有的训练脚本；这个 demo 主要用 `src/gpt2_prompt_demo/` 里的推理代码。

## 1. 创建虚拟环境

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Windows Command Prompt:

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

如果 PowerShell 阻止脚本执行，可以先运行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. 网页界面

启动本地网页服务：

```bash
python -m gpt2_prompt_demo.web
```

然后在浏览器里打开：

```text
http://127.0.0.1:8000
```

也可以指定模型或端口：

```bash
python -m gpt2_prompt_demo.web \
  --model gpt2 \
  --port 8010
```

页面里可以直接修改：

- prompt
- 模型名
- `max_new_tokens`
- `temperature`
- `top_k`
- `top_p`
- `seed`

## 3. 直接生成

默认模型是 `gpt2`：

```bash
python -m gpt2_prompt_demo --prompt "Once upon a time"
```

也可以指定更多参数：

```bash
python -m gpt2_prompt_demo \
  --prompt "The future of AI is" \
  --max-new-tokens 120 \
  --temperature 0.8 \
  --top-p 0.92
```

## 4. 交互模式

```bash
python -m gpt2_prompt_demo --interactive
```

输入 prompt 后会即时输出生成内容；输入 `exit`、`quit` 或空行即可退出。

## 5. 切换模型

默认 `gpt2` 更偏英文。如果你想试中文，可以换成一个中文 GPT-2 类模型，例如：

```bash
python -m gpt2_prompt_demo \
  --model uer/gpt2-chinese-cluecorpussmall \
  --prompt "从前有一座山"
```

## 6. 常用参数

- `--model`: 模型名，默认 `gpt2`
- `--prompt`: 单次生成输入
- `--interactive`: 开启交互模式
- `--max-new-tokens`: 新生成 token 数，默认 `80`
- `--temperature`: 采样温度，默认 `0.9`
- `--top-k`: top-k 采样，默认 `50`
- `--top-p`: nucleus 采样，默认 `0.95`
- `--seed`: 随机种子，默认 `42`
- `--device`: `auto`、`cpu`、`cuda`、`mps`
- `--cache-dir`: Hugging Face 模型缓存目录

网页模式额外支持：

- `--host`: 监听地址，默认 `127.0.0.1`
- `--port`: 端口，默认 `8000`

## 7. 注意事项

- 第一次运行会从 Hugging Face 下载模型，取决于网络环境可能较慢。
- 如果本机没有 GPU，会自动走 CPU，速度会慢一些。
- `gpt2` 原生更擅长英文文本；中文建议换模型。
- Windows 用户建议优先使用 PowerShell，并尽量用 `py -3` 来创建虚拟环境。
- Windows 路径里如果有空格，命令行参数中的本地路径建议加引号。

## 8. Hugging Face 下载慢或失败怎么办

如果你所在的网络环境访问 Hugging Face 较慢，可以考虑以下几种方式。

使用镜像站临时启动：

macOS / Linux:

```bash
HF_ENDPOINT=https://hf-mirror.com python -m gpt2_prompt_demo.web
```

Windows PowerShell:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
python -m gpt2_prompt_demo.web
```

Windows Command Prompt:

```bat
set HF_ENDPOINT=https://hf-mirror.com
python -m gpt2_prompt_demo.web
```

如果你想先下载到指定目录，也可以配合 `--cache-dir`：

```bash
python -m gpt2_prompt_demo \
  --model gpt2 \
  --cache-dir ./hf-cache \
  --prompt "Hello"
```

补充说明：

- `HF_ENDPOINT` 是给 Hugging Face Hub 客户端指定镜像地址的常见做法。
- 镜像站可用性取决于你当前网络环境和镜像服务状态。
- 如果模型已经下载过一次，之后通常会直接从本地缓存读取。
