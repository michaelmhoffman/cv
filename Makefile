## user variables
SRC = cv.md
SCHOLARID = 96r1DYUAAAAJ

## command variables
PANDOC = pandoc --smart --from=markdown+raw_tex
PANDOC_TOFILTER = $(PANDOC) --to=json
PANDOC_FINAL = $(PANDOC) --standalone --smart
PANDOC_DOCX = $(PANDOC_FINAL) --reference-docx=reference.docx
PANDOC_TEX = $(PANDOC_FINAL) --variable=geometry=margin=1in --variable=mainfont="TeX Gyre Heros" --variable=fontsize=12pt --include-in-header=preamble.tex --latex-engine=xelatex

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL) google-scholar.html cv-*.docx

.PHONY: all

## pattern rules

# using a pipeline because using --filter, a Python filter, and Cygwin python doesn't seem to work
%.docx : %.md reference.docx google-scholar.html
	$(PANDOC_TOFILTER) $< | ./panfilter.py | $(PANDOC_DOCX) --from=json -o $@

%.tex : %.md preamble.tex google-scholar.html
	$(PANDOC_TOFILTER) $< | ./panfilter.py | $(PANDOC_TEX) --from=json --to=latex | perl -pe 's/^([A-Z][0-9]+.)~/\\item[\1] /; s/\\(begin|end)enumerate/\\\1\{enumerate}/g' > $@

%.pdf : %.tex
	xelatex $<

%.html : %.md google-scholar.html
	$(PANDOC_TOFILTER) $< | ./panfilter.py | $(PANDOC_FINAL) --toc --from=json -o $@

%.json : %.md
	$(PANDOC) $< -o $@

cv-%.docx: cv.md %.yaml google-scholar.html
	$(PANDOC_TOFILTER) $< | ./panfilter.py --config=$(*F).yaml | $(PANDOC_DOCX) --from=json -o $@

## explicit rules

google-scholar.html:
	wget -O $@ https://scholar.google.com/citations?user=$(SCHOLARID)
