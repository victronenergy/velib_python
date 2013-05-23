PY:=/usr/bin/python2.7

all: tracing.pyo dbusitem.pyo settingsdevice.pyo

%.pyo: %.py $(DEPS)
	${PY} -O -m py_compile $<

clean:
	rm -f *.py? 

install: tracing.pyo dbusitem.pyo settingsdevice.pyo
	install -d ${DESTDIR}
	install -m 0755 $^ ${DESTDIR}

	
