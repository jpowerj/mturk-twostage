"""
Just a quick program that takes the hit_page.html and surrounds it by html
that lets you view it directly in a browser
"""

def main():
    with open("mturk_hit_page.html", 'r', encoding='utf-8') as f:
        raw_html = f.read()
    new_html = "<!DOCTYPE html><html><head><title>HIT Preview</title></head><body>" + raw_html
    new_html = new_html + "</body></html>"
    output_fpath = "mturk_hit_preview.html"
    with open(output_fpath, 'w', encoding='utf-8') as g:
        g.write(new_html)
    print(f"Preview html written to {output_fpath}")

if __name__ == "__main__":
    main()