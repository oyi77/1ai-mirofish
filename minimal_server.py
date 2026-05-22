#!/usr/bin/env python
"""
Minimal MiroFish backend - just the signals API with Polymarket optimization.
"""

import os
import json
import asyncio
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}


def create_app():
    return app


@app.route("/api/simulation/signals", methods=["GET"])
def get_prediction_signals():
    try:
        import httpx

        question = request.args.get("question", "")
        if not question:
            return jsonify({"signals": [], "message": "No question provided"})

        # Try to fetch Polymarket data
        market_data = None
        try:
            gamma_url = "https://gamma-api.polymarket.com"
            data_url = "https://data-api.polymarket.com"

            # Search more specifically
            async def fetch_data():
                async with httpx.AsyncClient(timeout=15.0) as client:
                    # Search for market with multiple attempts
                    search_terms = [
                        question.lower().replace(" ", "-"),
                        question.lower(),
                    ]

                    for term in search_terms[:1]:
                        resp = await client.get(
                            f"{gamma_url}/markets",
                            params={"question": term, "limit": 3},
                        )
                        if resp.status_code == 200:
                            markets = resp.json()
                            if markets:
                                # Find best match
                                for m in markets:
                                    q = m.get("question", "").lower()
                                    if any(
                                        w in q for w in question.lower().split()[:3]
                                    ):
                                        return m
                                return markets[0]
                    return None

            market_data = asyncio.run(fetch_data())
        except Exception as e:
            print(f"Market fetch error: {e}")

        # Build context
        context = ""
        price = 0.5
        volume = 0
        liquidity = 0

        if market_data:
            price = float(market_data.get("yesPrice", 0.5))
            volume = float(market_data.get("volume", 0))
            liquidity = float(market_data.get("liquidity", 0))

            context = f"""
MARKET DATA:
- YES price: {price:.4f}
- 24h volume: ${volume:,.0f}
- Liquidity: ${liquidity:,.0f}
- Resolved: {market_data.get('closed', False)}
"""

        # Call LLM
        try:
            from openai import OpenAI

            api_key = os.environ.get("LLM_API_KEY")
            base_url = os.environ.get("LLM_BASE_URL", "https://api.groq.com/v1")
            model = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

            client = OpenAI(api_key=api_key, base_url=base_url)

            prompt = f"""You are a prediction market analyst.

QUESTION: {question}{context}

Respond in JSON: {{"prediction": 0.0-1.0, "confidence": 0.0-1.0, "reasoning": "..."}}

Rules:
- Use market data if available
- Higher volume = higher confidence
- Keep reasoning short"""

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            data = json.loads(resp.choices[0].message.content)

            prediction = float(data.get("prediction", 0.5))
            confidence = float(data.get("confidence", 0.5))

            # Adjust confidence based on volume
            if volume > 10000:
                confidence = min(1.0, confidence + 0.1)
            if liquidity > 5000:
                confidence = min(1.0, confidence + 0.1)

            signal = {
                "market_id": question[:100],
                "prediction": max(0.0, min(1.0, prediction)),
                "confidence": max(0.0, min(1.0, confidence)),
                "reasoning": data.get("reasoning", "Analysis complete"),
                "source": "mirofish-polymarket",
            }

            return jsonify(
                {
                    "signals": [signal],
                    "market": "polymarket",
                    "question": question,
                    "market_data": (
                        {"price": price, "volume": volume, "liquidity": liquidity}
                        if market_data
                        else None
                    ),
                }
            )

        except Exception as e:
            return jsonify({"signals": [], "error": str(e)}), 500

    except Exception as e:
        return jsonify({"signals": [], "error": str(e)}), 500


if __name__ == "__main__":
    print("Starting minimal MiroFish on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=False)
