# cv

Converts a curriculum vitae (CV) written in Pandoc Markdown to a variety of
other formats (docx, html).

You can use config files in YAML format to exclude sections of the CV
based on title or age.

This package will also insert numbers of citations from a `google-scholar.html`
file that you download from your own Google Scholar Citations page.

## Prerequisites

Pandoc is required.

Python prerequisites
```
pip install PyYAML beautifulsoup4 jinja2
```

## Debugging

To debug `panfilter.py` it's often helpful to `make` the intermediate
`.json` file it uses. Then you can run `panfilter something.json`
under the Python debugger instead of using pipes.

## License

License for software, config files, and Jinja directives in
`cv.md.jinja`: GNU General Public License v2.

No license is provided for the text contents of Michael Hoffman's CV
(`cv.md.jinja`). Make your own!

## Support

Absolutely no support is provided.
