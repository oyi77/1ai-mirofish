"""
Polymarket data client for MiroFish signal optimization.
Fetches real-time market data, order books, whale positions, and historical resolution.
Uses PolyEdge shared service when available, falls back to direct Polymarket APIs.
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import httpx

logger = logging.getLogger('mirofish.polymarket')


class PolymarketClient:
    """
    Client for fetching Polymarket data for signal optimization.
    Tries PolyEdge shared service first, falls back to direct Polymarket APIs.
    """
    
    def __init__(
        self,
        gamma_url: str = "https://gamma-api.polymarket.com",
        data_url: str = "https://data-api.polymarket.com",
        clob_url: str = "https://clob.polymarket.com",
        use_shared_service: bool = True,
        polyedge_url: str = "http://localhost:8000",
        polyedge_api_key: str = "",
    ):
        self.gamma_url = gamma_url
        self.data_url = data_url
        self.clob_url = clob_url
        self.use_shared_service = use_shared_service
        self.polyedge_url = polyedge_url
        self.polyedge_api_key = polyedge_api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._init_lock = asyncio.Lock()
    
    async def _get_client(self) -> httpx.AsyncClient:
        async with self._init_lock:
            if self._client is None:
                self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _try_polyedge(self, url: str, params: Optional[dict] = None) -> Optional[Any]:
        """Try PolyEdge shared service with 3 retries, return None on failure."""
        if not self.use_shared_service:
            return None
        headers = {"X-API-Key": self.polyedge_api_key} if self.polyedge_api_key else {}
        for attempt in range(3):
            try:
                client = await self._get_client()
                resp = await client.get(url, params=params, headers=headers, timeout=5.0)
                if resp.status_code == 429:
                    await asyncio.sleep(60)
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                else:
                    logger.warning(
                        f"Using direct Polymarket API - PolyEdge shared service unavailable ({url}): {e}"
                    )
                    return None
        return None

    async def find_market(self, question: str) -> Optional[Dict[str, Any]]:
        data = await self._try_polyedge(
            f"{self.polyedge_url}/api/v1/data/polymarket/markets",
            params={"question": question, "limit": 5}
        )
        if data is not None:
            markets = data if isinstance(data, list) else data.get("markets", [])
            if markets:
                return markets[0]

        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.gamma_url}/markets",
                params={"question": question, "limit": 5}
            )
            resp.raise_for_status()
            markets = resp.json()
            return markets[0] if markets else None
        except Exception as e:
            logger.warning(f"Failed to find market '{question}': {e}")
            return None
    
    async def get_market_price(self, condition_id: str) -> Optional[float]:
        data = await self._try_polyedge(
            f"{self.polyedge_url}/api/v1/data/polymarket/price/{condition_id}"
        )
        if data is not None:
            price = data.get("yes_price") or data.get("yesPrice") or data.get("price")
            if price is not None:
                return float(price)

        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.gamma_url}/markets",
                params={"conditionId": condition_id}
            )
            resp.raise_for_status()
            markets = resp.json()
            if not markets:
                return None
            return float(markets[0].get('yesPrice', 0.5))
        except Exception as e:
            logger.warning(f"Failed to get price for {condition_id}: {e}")
            return None
    
    async def get_order_book(self, token_id: str) -> Optional[Dict[str, Any]]:
        data = await self._try_polyedge(
            f"{self.polyedge_url}/api/v1/data/polymarket/orderbook/{token_id}"
        )
        if data is not None:
            return data

        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.clob_url}/order_book",
                params={"token_id": token_id}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Failed to get order book for {token_id}: {e}")
            return None
    
    async def analyze_liquidity(self, token_id: str) -> Dict[str, Any]:
        """
        Analyze liquidity: spread, depth, volume.
        """
        client = await self._get_client()
        
        result = {
            "spread": None,
            "bid_depth": 0.0,
            "ask_depth": 0.0,
            "volume_24h": 0.0,
            "liquidity_score": 0.0
        }
        
        try:
            # Get market data
            resp = await client.get(
                f"{self.gamma_url}/markets",
                params={"tokenId": token_id}
            )
            resp.raise_for_status()
            markets = resp.json()
            
            if markets:
                m = markets[0]
                result["volume_24h"] = float(m.get('volume', 0))
                result["liquidity_score"] = float(m.get('liquidity', 0))
            
            # Get order book for spread
            resp = await client.get(
                f"{self.clob_url}/order_book",
                params={"token_id": token_id}
            )
            resp.raise_for_status()
            book = resp.json()
            
            bids = book.get('bids', [])[:5]
            asks = book.get('asks', [])[:5]
            
            if bids and asks:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                result["spread"] = best_ask - best_bid
                
                # Depth (sum of top 5)
                result["bid_depth"] = sum(float(b[1]) for b in bids)
                result["ask_depth"] = sum(float(a[1]) for a in asks)
            
            logger.info(f"Liquidity analysis: spread={result['spread']}, vol={result['volume_24h']}")
            
        except Exception as e:
            logger.warning(f"Liquidity analysis failed: {e}")
        
        return result
    
    async def get_whale_positions(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top whale positions from leaderboard.
        """
        client = await self._get_client()
        
        try:
            resp = await client.get(
                f"{self.data_url}/leaderboard",
                params={"window": "30d", "limit": top_n}
            )
            resp.raise_for_status()
            return resp.json()
            
        except Exception as e:
            logger.warning(f"Failed to get whale positions: {e}")
            return []
    
    async def get_trader_positions(self, wallet: str) -> List[Dict[str, Any]]:
        """
        Get positions for a specific wallet.
        """
        client = await self._get_client()
        
        try:
            resp = await client.get(
                f"{self.data_url}/positions",
                params={"user": wallet, "sizeThreshold": "1.0"}
            )
            resp.raise_for_status()
            return resp.json()
            
        except Exception as e:
            logger.warning(f"Failed to get positions for {wallet}: {e}")
            return []
    
    async def get_market_history(self, condition_id: str) -> Dict[str, Any]:
        """
        Get historical resolution stats for a market.
        """
        client = await self._get_client()
        
        result = {
            "resolved": False,
            "outcome": None,
            "end_date": None
        }
        
        try:
            resp = await client.get(
                f"{self.gamma_url}/markets",
                params={"conditionId": condition_id}
            )
            resp.raise_for_status()
            markets = resp.json()
            
            if markets:
                m = markets[0]
                result["resolved"] = m.get('closed', False) or m.get('resolved', False)
                
                if result["resolved"]:
                    outcome = m.get('outcome')
                    if isinstance(outcome, dict):
                        result["outcome"] = outcome.get('title', outcome.get('winner', 'Unknown'))
                    else:
                        result["outcome"] = outcome
                
                if m.get('endDate'):
                    result["end_date"] = m.get('endDate')
            
        except Exception as e:
            logger.warning(f"Failed to get history for {condition_id}: {e}")
        
        return result
    
    async def get_market_stats(self, question: str) -> Dict[str, Any]:
        """
        Get comprehensive market stats for signal generation.
        """
        stats = {
            "found": False,
            "condition_id": None,
            "token_id": None,
            "current_price": 0.5,
            "volume": 0.0,
            "liquidity": 0.0,
            "spread": None,
            "bid_depth": 0.0,
            "ask_depth": 0.0,
            "whale_positions": [],
            "resolved": False,
            "outcome": None,
            "error": None
        }
        
        try:
            # Find market
            market = await self.find_market(question)
            if not market:
                stats["error"] = "Market not found"
                return stats
            
            stats["found"] = True
            stats["condition_id"] = market.get('conditionId')
            stats["token_id"] = market.get('tokenId')
            
            # Get price
            price = await self.get_market_price(stats["condition_id"])
            if price:
                stats["current_price"] = price
            
            # Get volume
            stats["volume"] = float(market.get('volume', 0))
            stats["liquidity"] = float(market.get('liquidity', 0))
            
            # Get liquidity
            if stats["token_id"]:
                liq = await self.analyze_liquidity(stats["token_id"])
                stats["spread"] = liq.get("spread")
                stats["bid_depth"] = liq.get("bid_depth")
                stats["ask_depth"] = liq.get("ask_depth")
            
            # Get whale positions
            whales = await self.get_whale_positions(top_n=5)
            stats["whale_positions"] = [
                {"wallet": w.get("user"), "pnl": w.get("pnl"), "volume": w.get("volume")}
                for w in whales[:5]
            ]
            
            # Get resolution history
            history = await self.get_market_history(stats["condition_id"])
            stats["resolved"] = history.get("resolved", False)
            stats["outcome"] = history.get("outcome")
            
            logger.info(f"Market stats for '{question[:40]}': price={stats['current_price']}, vol={stats['volume']}")
            
        except Exception as e:
            stats["error"] = str(e)
            logger.warning(f"Failed to get market stats: {e}")
        
        return stats


# Singleton instance
_client: Optional[PolymarketClient] = None


def get_polymarket_client() -> PolymarketClient:
    global _client
    if _client is None:
        from ..config import Config
        _client = PolymarketClient(
            gamma_url=Config.POLYMARKET_GAMMA_URL,
            data_url=Config.POLYMARKET_DATA_URL,
            clob_url=Config.POLYMARKET_CLOB_URL,
            use_shared_service=True,
            polyedge_url=os.getenv("POLYEDGE_URL", "http://localhost:8000"),
            polyedge_api_key=os.getenv("MIROFISH_API_KEY", ""),
        )
    return _client