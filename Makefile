PY:=/usr/bin/python2.7

all: tracing.pyo

%.pyo: %.py $(DEPS)
	${PY} -O -m py_compile $<

clean:
	rm -f *.py? 

install: tracing.pyo
	install -d ${DESTDIR}
	install -m 0755 $^ ${DESTDIR}

	
