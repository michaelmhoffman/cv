## variables
SRC = cv.md
PANDOC = pandoc
PANDOCFINAL = $(PANDOC) --standalone --smart
PANDOCDOCX = $(PANDOCFINAL) --reference-docx=reference.docx

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL)

.PHONY: all

## pattern rules

%.docx : %.md
	$(PANDOCDOCX) $< -o $@

%.html : %.md
	$(PANDOCFINAL) --toc $< -o $@

%.json : %.md
	$(PANDOC) $< -o $@

cv-%.docx: cv.md %.yaml
	$(PANDOC) --smart --to=json $< | ./panfilter.py --config=$(*F).yaml | $(PANDOCDOCX) --from=json -o $@

## explicit rules

