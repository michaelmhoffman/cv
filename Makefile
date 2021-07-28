## user variables
SRC = cv.md
SCHOLARID = 96r1DYUAAAAJ
PANFILTER_FLAGS =
HMARGIN = 1in
VMARGIN = 1in

## command variables
JINJA_FLAGS_PRIVATE = --search-dir=../cv-private --set private
JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE)
JINJA = ./jinja.py $(JINJA_FLAGS)

LATEX = lualatex

PANDOC = pandoc
PANDOC_TOJSON = $(PANDOC) --from=markdown+raw_tex --to=json
PANDOC_FINAL = $(PANDOC) --standalone --variable=lang:en
PANDOC_DOCX = $(PANDOC_FINAL) --reference-doc=reference.docx
PANDOC_TEX = $(PANDOC_FINAL) \
	--variable=geometry:hmargin=$(HMARGIN),vmargin=$(VMARGIN) \
	--variable=mainfont:"TeX Gyre Heros" \
	--variable=fontsize:12pt \
	--variable=subparagraph \
	--variable=colorlinks \
	--include-in-header=preamble.tex \
	--pdf-engine=$(LATEX) \
	--to=latex

PANFILTER = ./panfilter.py $(PANFILTER_FLAGS)

RM = rm -f
PYTHON = python2
PIP = $(PYTHON) -m pip

PYTHON_DEPS = jinja2 bs4 PyYAML lxml

# XXX: \beginenumerate etc. could be made a TeX macro rather than filtering here
TEXFILTER = perl -pe 's/^([A-Z]+[0-9]+.)~/\\item[\1] /; s/\\(begin|end)enumerate/\\\1\{enumerate}/g'

SCHOLARURL=https://scholar.google.com/citations?user=$(SCHOLARID)

## phony targets
ALL=$(SRC:.md=-default.docx) $(SRC:.md=-default.html) $(SRC:.md=-default.pdf)

all: $(ALL) web

installdeps-sudo-debian:
	sudo apt install pandoc texlive-xetex
	sudo --set-home pip install $(PYTHON_DEPS)

installdeps-python:
	$(PIP) install $(PYTHON_DEPS)

web: cv-web.pdf
	scp cv-web.pdf mordor:~/public_html/cv/michael-hoffman-cv.pdf

github: cv-web.pdf cv-web.docx
	cp cv-web.pdf cv.pdf
	cp cv-web.docx cv.docx
	gh release upload latest cv.pdf cv.docx --clobber

mostlyclean:
	-$(RM) cv-*.md cv-*.tex cv-*.docx cv-*.pdf cv-*.json *.aux *.out *.log *.synctex.gz *.fdb_latexmk empty.yaml

clean: mostlyclean
	-$(RM) cookies.txt google-scholar.html

.PHONY: all mostlyclean clean web installdeps-sudo-debian

.INTERMEDIATE: cv-empty.json

## pattern rules

%.json : %.md
	$(PANDOC_TOJSON) $< -o $@

# XXX: change everything to cv-%-%.*: to separate template and yaml config
# XXX: use jinja2.meta.find_referenced_templates to automake deps
cv-%.md : cv.md.jinja
	$(JINJA) $< $@

# debugging:
# variant=crs
# make "cv-${variant}.json"
# PYTHONINSPECT=1 ./panfilter.py --config="${variant}.yaml" "cv-${variant}.json"

# using a pipeline because using --filter, a Python filter, and Cygwin python doesn't seem to work
cv-%.docx: cv-%.md reference.docx google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_DOCX) --from=json -o $@
	cp $@ cv.docx

cv-%.html : cv-%.md google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_FINAL) --toc --from=json -o $@

cv-%.tex : cv-%.md preamble.tex google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_TEX) --from=json | $(TEXFILTER) > $@

%.pdf : %.tex
	fottexmk -$(LATEX) $<
	cp $@ cv.pdf

%.yaml :
	touch $@

# XXX: Jinja include dependencies not included

## explicit rules

# empty.yaml: empty yaml, can copy to new YAMLs
# XXX: Google Scholar shouldn't be required strictly speaking
empty.yaml: cv-empty.json google-scholar.html
	$(PANFILTER) --verbose $< 2>&1 >/dev/null | sed -e 's/^including/- id:/' > $@

# all: everything
cv-all.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE)

all-public.yaml : all.yaml
	cp $< $@

cv-all-public.md : JINJA_FLAGS =

cv-all-nostartup.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set nostartup

# crs:
cv-crs.md : cv-crs.md.jinja
	$(JINJA) $< $@

# scn: Stem Cell Network
cv-scn.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --abbr-months --set compact
cv-scn.tex : HMARGIN = 0.5in
cv-scn.tex : VMARGIN = \{0.5in,0.75in\}

# select: Selected stuff only
cv-select.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set select

# select-nostartup: selected stuff without startup
select-nostartup.yaml : select.yaml
	cp $< $@
cv-select-nostartup.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set select --set nostartup

# compact: Selected stuff only without startup, compact style
compact.yaml : select.yaml
	cp $< $@
cv-compact.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set select --set nostartup --set compact --abbr-months --set presentation_score=750

cv-compact.tex : HMARGIN = 0.5in
cv-compact.tex : VMARGIN = \{0.5in,0.75in\}

# rsc: Royal Society of Canada
cv-rsc.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set select --set nostartup --set compact --set annotate --abbr-months --set presentation_score=0

cv-rsc.tex : HMARGIN = 0.5in
cv-rsc.tex : VMARGIN = \{0.5in,0.75in\}

# nostartup: everything except startup
cv-nostartup.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set nostartup

# statusonly: Include "status-only" for those who care about it
cv-statusonly.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set statusonly --set nostartup

# web: default public web view
cv-web.md : JINJA_FLAGS =

google-scholar.html: cookies.txt
	wget --load-cookies=$< -O $@ $(SCHOLARURL)

cookies.txt:
	wget --save-cookies=$@ -O /dev/null $(SCHOLARURL)
