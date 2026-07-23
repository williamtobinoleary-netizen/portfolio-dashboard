import json
import urllib.request
import urllib.error


LLAMA_API_URL = "http://127.0.0.1:8080/v1/chat/completions"
DEFAULT_MODEL = "C:\\models\\Llama-3.2-3B-Instruct-Q4_K_M.gguf"


def build_system_prompt(portfolio_summary: str | None = None) -> str:
    base = (
        "You are a helpful financial assistant integrated into a portfolio analytics dashboard. "
        "Answer questions about portfolio data, investing, and financial concepts. "
        "Be concise and use plain English. "
        "You are NOT a financial advisor — always remind users this is for educational purposes only."
    )
    if portfolio_summary:
        base += f"\n\nCurrent portfolio data:\n{portfolio_summary}"
    return base


def get_portfolio_summary(df, total_value, portfolio_return, historical_performance, tickers) -> str:
    lines = [f"Holdings ({len(df)} positions):"]
    for _, row in df.iterrows():
        lines.append(f"  - {row['Ticker']}: {row['Shares']} shares @ £{row.get('Price', 'N/A')} = £{row.get('Value', 'N/A'):.2f}")
    lines.append(f"Total value: £{total_value:,.2f}")
    if portfolio_return is not None:
        lines.append(f"Portfolio return: {portfolio_return:.2f}%")
    if historical_performance and historical_performance.get("annualized_return"):
        lines.append(f"Annualized return: {historical_performance['annualized_return']*100:.2f}%")
    return "\n".join(lines)


def chat(messages: list[dict], model: str | None = None, timeout: int = 60) -> str | None:
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 512,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LLAMA_API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"Server error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return f"Connection error: {e.reason}. Make sure your llama.cpp server is running."
    except Exception as e:
        return f"Error: {e}"
