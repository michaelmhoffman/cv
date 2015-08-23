## user variables
SRC = cv.md
SCHOLARID = 96r1DYUAAAAJ

## command variables
PANDOC = pandoc
PANDOCTOFILTER = $(PANDOC) --smart --to=json
PANDOCFINAL = $(PANDOC) --standalone --smart
PANDOCDOCX = $(PANDOCFINAL) --reference-docx=reference.docx

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL) google-scholar.html cv-*.docx

.PHONY: all

## pattern rules

# using a pipeline because using --filter, a Python filter, and Cygwin python doesn't seem to work
%.docx : %.md google-scholar.html
	$(PANDOCTOFILTER) $< | ./panfilter.py | $(PANDOCDOCX) --from=json -o $@

%.html : %.md google-scholar.html
	$(PANDOCTOFILTER) $< | ./panfilter.py | $(PANDOCFINAL) --toc --from=json -o $@

%.json : %.md
	$(PANDOC) $< -o $@

cv-%.docx: cv.md %.yaml google-scholar.html
	$(PANDOCTOFILTER) $< | ./panfilter.py --config=$(*F).yaml | $(PANDOCDOCX) --from=json -o $@

## explicit rules

google-scholar.html:
	wget -O $@ https://scholar.google.com/citations?user=$(SCHOLARID)
