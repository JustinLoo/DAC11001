#PROJECT=opa855X4_YL

COMMITNUM = $(shell git log --pretty=oneline --abbrev-commit --abbrev=8|head -1 | awk '{print $$1}')
DATETIME = $(shell date  +'%Y%m%d%H%M%S')
GITTIME=$(shell git log -1 --date=iso-strict --pretty=%cd)

PROJECT := $(shell basename $(CURDIR))
pdf:
	kicad-cli sch export pdf $(PROJECT).kicad_sch

fab: gerber.py
	mkdir -p fab
	python scripts/gerber.py $(PROJECT).kicad_pcb fab -gerber -drill -bom -xypos
gerber.py:
	mkdir -p scripts
	wget https://gitlab.com/lbl-bids/kicad_library/-/raw/master/scripts/gerber.py -O scripts/gerber.py
pcb_rmfield:
	python ../scripts/pcb_fp_remove_fields.py $(PROJECT).kicad_pcb Vendor
gerberpdf:
	for f in `ls fab/*.gbr`; do gerbv $f -x pdf -o $f.pdf; done
SCHFILE := $(shell git ls-files ./*.kicad_sch)
PCBFILE := $(shell git ls-files ./*.kicad_pcb)
PROFILE := $(shell git ls-files ./*.kicad_pro)

gitify:
	@for file in $(SCHFILE); do \
		python3 ../scripts/gitifykicad.py "$$file"; \
	done
	@for file in $(PCBFILE); do \
		python3 ../scripts/gitifykicad.py "$$file"; \
	done
	@for file in $(PROFILE); do \
		python3 ../scripts/gitifykicad.py "$$file"; \
	done

tarball: fab
	echo $(GITTIME)
	tar --sort=name --mtime=$(GITTIME)  --owner=0 --group=0 --numeric-owner -czf $(PROJECT)_$(DATETIME)_$(COMMITNUM).tar.gz fab 
	md5sum $(PROJECT)_$(DATETIME)_$(COMMITNUM).tar.gz
zip: fab
	touch -d $(GITTIME) fab/* 
	zip -X -o $(PROJECT)_$(DATETIME)_$(COMMITNUM).zip fab/* 
	md5sum $(PROJECT)_$(DATETIME)_$(COMMITNUM).zip

clean:
	rm -rf fab

.PHONY: gerber.py fab
