import json
import os
from build import build

def test_titles_appear_in_output():
    build()
    
    # Check paths from L8/ or workspace root
    html_path = "site/index.html"
    data_path = "data.json"
    
    if not os.path.exists(html_path) and os.path.exists("L8/site/index.html"):
        html_path = "L8/site/index.html"
        data_path = "L8/data.json"
        
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(data_path, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    for item in items:
        assert item["title"] in html
