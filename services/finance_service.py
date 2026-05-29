import requests
import re

def get_market_data():
    """Obtiene la cotización actual usando endpoints web sin bloqueos (Gratis, sin API Key)."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Bitcoin from CoinGecko
    try:
        btc_res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", headers=headers, timeout=10)
        btc_price = btc_res.json()["bitcoin"]["usd"]
        btc_str = f"- Bitcoin: {btc_price:,.2f} USD"
    except Exception as e:
        btc_str = f"- Bitcoin: Error ({e})"
        
    # S&P 500 from Yahoo API
    try:
        sp_res = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC", headers=headers, timeout=10)
        if sp_res.status_code == 200:
            data = sp_res.json()
            sp_price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            sp_str = f"- S&P 500: {sp_price:,.2f} USD"
        else:
            sp_str = f"- S&P 500: Error {sp_res.status_code}"
    except Exception as e:
        sp_str = f"- S&P 500: Error ({e})"
        
    return f"📈 *Mercados:*\n{sp_str}\n{btc_str}"
