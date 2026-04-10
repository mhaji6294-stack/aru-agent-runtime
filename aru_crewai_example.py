import os
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from aru_crewai import ARUToolWrapper

class BTCPriceTool(BaseTool):
    name: str = "Get BTC Price"
    description: str = "Fetch current Bitcoin price from CoinGecko for a given currency."

    def _run(self, currency: str = "usd") -> str:
        import urllib.request, json
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return f"BTC/{currency.upper()}: {data['bitcoin'][currency]}"

llm = LLM(model="claude-opus-4-5", api_key=os.environ["ANTHROPIC_API_KEY"])
certified_btc = ARUToolWrapper(BTCPriceTool())

analyst = Agent(
    role="Market Analyst",
    goal="Provide accurate crypto market data",
    backstory="You are a professional crypto analyst who fetches and reports live market data.",
    tools=[certified_btc],
    llm=llm,
    verbose=True
)

task = Task(
    description="Get the current Bitcoin price in USD. Report the value clearly.",
    expected_output="Bitcoin price in USD with ARU certification ID.",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task], verbose=True)

if __name__ == "__main__":
    print("\n[ARU] Starting certified crew execution...\n")
    result = crew.kickoff()
    print("\n=== Result ===")
    print(result)
    print("\n=== Cert Ledger ===")
    if os.path.exists("aru_cert_ledger.jsonl"):
        with open("aru_cert_ledger.jsonl") as f:
            print(f.read())
