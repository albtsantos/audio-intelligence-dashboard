import os

css_filepaths = [f for f in os.listdir() if f.endswith(".css")]

css_filepaths.remove('page.css')
css_filepaths.insert(0, 'page.css')

css = ""
for filepath in css_filepaths:
    with open(filepath, 'r') as file:
        css += file.read()

with open("../styles.css", 'w') as f:
    f.write(css)