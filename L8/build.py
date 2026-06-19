import json
import os

def build():
    # Make paths work both from workspace root and L8/ directory
    data_path = "data.json"
    site_dir = "site"
    
    if not os.path.exists(data_path) and os.path.exists("L8/data.json"):
        data_path = "L8/data.json"
        site_dir = "L8/site"
        
    with open(data_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head><title>My list</title></head>")
    lines.append("<body>")
    lines.append("<h1>My list</h1>")
    lines.append("<ul>")
    for item in items:
        lines.append(f"  <li><strong>{item['title']}</strong>: {item['description']}</li>")
    lines.append("</ul>")
    lines.append("</body>")
    lines.append("</html>")

    os.makedirs(site_dir, exist_ok=True)
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Site built successfully in '{site_dir}/index.html'.")

if __name__ == "__main__":
    build()
