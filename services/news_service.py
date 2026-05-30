import feedparser

def get_top_financial_news():
    """Obtiene la noticia financiera más importante del día usando Google News RSS (Gratis, sin API Key)."""
    # RSS de Google News España para temas de Economía
    url = "https://news.google.com/rss/search?q=economia+finanzas+when:1d&hl=es&gl=ES&ceid=ES:es"
    
    try:
        feed = feedparser.parse(url)
        
        if feed.entries:
            article = feed.entries[0]
            title = article.title.replace('*', '').replace('_', ' ').replace('[', '').replace(']', '')
            link = article.link.replace('_', '%5F')
            
            return f"📰 *Noticia financiera destacada:*\n*{title}*\n[Leer más]({link})"
        else:
            return "📰 No se encontraron noticias financieras relevantes recientes."
            
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "📰 Hubo un error al obtener las noticias."
