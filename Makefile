## variables
SRC = cv.md
PANDOC = pandoc
PANDOCFINAL = $(PANDOC) --standalone --smart

## phony targets
ALL=$(SRC:.md=.docx) $(SRC:.md=.html)

all: $(ALL)

clean:
	-rm $(ALL)

.PHONY: all

## pattern rules

%.docx : %.md
	$(PANDOCFINAL) $< -o $@

%.html : %.md
	$(PANDOCFINAL) --toc $< -o $@

cv-%.docx: cv.md include-%.txt
	$(PANDOC) $< --to=json | ./panfilter.py --include-from=include-$(*F).txt | $(PANDOCFINAL) --from=json -o $@

## explicit rules

