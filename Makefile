## user variables
SRC = cv.md
SCHOLARID = 96r1DYUAAAAJ
PANFILTER_FLAGS =

## command variables
PANDOC = pandoc --smart --from=markdown+raw_tex
PANDOC_TOFILTER = $(PANDOC) --to=json
PANDOC_FINAL = $(PANDOC) --standalone --smart
PANDOC_DOCX = $(PANDOC_FINAL) --reference-docx=reference.docx
PANDOC_TEX = $(PANDOC_FINAL) --variable=geometry=margin=1in --variable=mainfont="TeX Gyre Heros" --variable=fontsize=12pt --include-in-header=preamble.tex --latex-engine=xelatex --to=latex

PANFILTER = ./panfilter.py $(PANFILTER_FLAGS)
PANFILTER_DEFAULT = $(PANFILTER) --config=default.yaml

# XXX: \beginenumerate etc. could be made a TeX macro rather than filtering here
TEXFILTER = perl -pe 's/^([A-Z][0-9]+.)~/\\item[\1] /; s/\\(begin|end)enumerate/\\\1\{enumerate}/g'

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html) $(SRC:.md=.pdf) web

all: $(ALL)

web: cv-web.pdf
	scp cv-web.pdf mordor:~/public_html/cv/michael-hoffman-cv.pdf

clean:
	-rm $(ALL) google-scholar.html cv-*.docx

.PHONY: all clean web

## pattern rules

%.json : %.md
	$(PANDOC) $< -o $@

% : %.jinja
	./jinja.py $< $@

# using a pipeline because using --filter, a Python filter, and Cygwin python doesn't seem to work
%.docx : %.md reference.docx google-scholar.html default.yaml
	$(PANDOC_TOFILTER) $< | $(PANFILTER_DEFAULT) | $(PANDOC_DOCX) --from=json -o $@

cv-%.docx: cv.md reference.docx google-scholar.html %.yaml
	$(PANDOC_TOFILTER) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_DOCX) --from=json -o $@

%.html : %.md google-scholar.html default.yaml
	$(PANDOC_TOFILTER) $< | $(PANFILTER_DEFAULT) | $(PANDOC_FINAL) --toc --from=json -o $@

%.tex : %.md preamble.tex google-scholar.html default.yaml
	$(PANDOC_TOFILTER) $< | $(PANFILTER_DEFAULT) | $(PANDOC_TEX) --from=json | $(TEXFILTER) > $@

cv-%.tex : cv.md preamble.tex google-scholar.html %.yaml
	$(PANDOC_TOFILTER) $< | $(PANFILTER) --config=$(*F).yaml | $(PANDOC_TEX) --from=json | $(TEXFILTER) > $@

%.pdf : %.tex
	xelatex $<

## explicit rules

google-scholar.html:
	wget -O $@ https://scholar.google.com/citations?user=$(SCHOLARID)
