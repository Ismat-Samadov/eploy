import re
import json
from scrapfly import ScrapflyClient, ScrapeConfig

client = ScrapflyClient(key="YOUR SCRAPFLY KEY")

def extract_apollo_state(html):
    """Extract apollo graphql state data from HTML source"""
    data = re.findall('apolloState":\s*({.+})};', html)[0]
    return json.loads(data)


def scrape_overview(company_name: str, company_id: str) -> dict:
    url = f"https://www.glassdoor.com/Overview/Working-at-{company_name}-EI_IE{company_id}.htm"
    result = client.scrape(ScrapeConfig(url, country="US", cookies={"tldp": "1"}))
    apollo_state = extract_apollo_state(result.content)
    return next(v for k, v in apollo_state.items() if k.startswith("Employer:"))


print(json.dumps(scrape_overview("eBay", "7853"), indent=2))
