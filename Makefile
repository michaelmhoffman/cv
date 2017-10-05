## user variables
SRC = cv.md
SCHOLARID = 96r1DYUAAAAJ
PANFILTER_FLAGS =
HMARGIN = 1in
VMARGIN = 1in

## command variables
JINJA_FLAGS_PRIVATE = --search-dir=../cv-private
JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE)

PANDOC = pandoc
PANDOC_TOJSON = $(PANDOC) --smart --from=markdown+raw_tex --to=json
PANDOC_FINAL = $(PANDOC) --standalone --smart --variable=lang:en
PANDOC_DOCX = $(PANDOC_FINAL) --reference-docx=reference.docx
PANDOC_TEX = $(PANDOC_FINAL) \
	--variable=geometry:hmargin=$(HMARGIN),vmargin=$(VMARGIN) \
	--variable=mainfont:"TeX Gyre Heros" \
	--variable=fontsize:12pt \
	--variable=subparagraph \
	--variable=colorlinks \
	--include-in-header=preamble.tex \
	--latex-engine=xelatex \
	--to=latex

PANFILTER = ./panfilter.py $(PANFILTER_FLAGS)

RM = rm -f

# XXX: \beginenumerate etc. could be made a TeX macro rather than filtering here
TEXFILTER = perl -pe 's/^([A-Z]+[0-9]+.)~/\\item[\1] /; s/\\(begin|end)enumerate/\\\1\{enumerate}/g'

SCHOLARURL=https://scholar.google.com/citations?user=$(SCHOLARID)

## phony targets
ALL=$(SRC:.md=-default.docx) $(SRC:.md=-default.html) $(SRC:.md=-default.pdf)

installdeps-sudo-debian:
	sudo apt install pandoc texlive-xetex
	sudo --set-home pip install jinja2 bs4 PyYAML lxml

all: $(ALL) web

web: cv-web.pdf
	scp cv-web.pdf mordor:~/public_html/cv/michael-hoffman-cv.pdf

mostlyclean:
	-$(RM) cv-*.{md,tex,docx,pdf} *.aux *.out *.log

clean: mostlyclean
	-$(RM) cookies.txt google-scholar.html

.PHONY: all mostlyclean clean web installdeps

## pattern rules

%.json : %.md
	$(PANDOC_TOJSON) $< -o $@

cv-%.md : cv.md.jinja
	./jinja.py $(JINJA_FLAGS) $< $@

# using a pipeline because using --filter, a Python filter, and Cygwin python doesn't seem to work
cv-%.docx: cv-%.md reference.docx google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_DOCX) --from=json -o $@

cv-%.html : cv-%.md google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_FINAL) --toc --from=json -o $@

cv-%.tex : cv-%.md preamble.tex google-scholar.html %.yaml
	$(PANDOC_TOJSON) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_TEX) --from=json | $(TEXFILTER) > $@

%.pdf : %.tex
	xelatex $<

%.yaml :
	touch $@

## explicit rules

# scn: Stem Cell Network
cv-scn.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --abbr-months --set compact
cv-scn.tex : HMARGIN = 0.5in
cv-scn.tex : VMARGIN = \{0.5in,0.75in\}

# select: Selected stuff only
cv-select.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set select

# statusonly: Include "status-only" for those who care about it
cv-statusonly.md : JINJA_FLAGS = $(JINJA_FLAGS_PRIVATE) --set statusonly

# web: default public web view
cv-web.md : JINJA_FLAGS =

google-scholar.html: cookies.txt
	wget --load-cookies=$< -O $@ $(SCHOLARURL)

cookies.txt:
	wget --save-cookies=$@ -O /dev/null $(SCHOLARURL)
