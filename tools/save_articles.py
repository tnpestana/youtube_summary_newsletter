import os
from datetime import datetime

def save_to_file(text, output_path=None):
    os.makedirs("summarized_articles", exist_ok=True)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join("summarized_articles", f"articles_{timestamp}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ All articles saved to: {output_path}")