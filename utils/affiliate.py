def build_amazon_url(asin, affiliate_tag):
    return f"https://www.amazon.com/dp/{asin}?tag={affiliate_tag}"

def build_walmart_url(item_id, affiliate_tag):
    return f"https://www.walmart.com/ip/{item_id}?affp={affiliate_tag}"
