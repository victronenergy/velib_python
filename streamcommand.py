#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package dbus_vrm

import logging
logger = logging.getLogger(__name__)

import threading
import subprocess
from time import sleep

# Runs a command, and calls sendfeedback with the statusupdates.
class StreamCommand(object):
	def run(self, command, timeout, feedbacksender, errorprefix = ""):
		self.feedbacksender = feedbacksender
		self.returncode = errorprefix,
		self.errorprefix = errorprefix

		def target():
			logger.info('Thread started for running %s' % command)
			self.feedbacksender.send({"status": "starting"})

			try:
				self.process = subprocess.Popen(command, stdout=subprocess.PIPE)
			except OSError as e:
				logger.info("Command %s could not be started, error: %s" % (command, e.strerror))
				self.feedbacksender.send({"status": "error", "errormessage": "Could not start", "errorcode": 731}, finished=True)

				self.process = None
				return

			self.readandsend()

			logger.info('Thread finished for running %s' % command)

		thread = threading.Thread(target=target)
		thread.start()
		thread.join(timeout)

		if self.process is None:
			# Error message (could_not_start) has already been sendfeedback-ed: nothing left to do
			return None

		# Make sure to send all the output
		self.readandsend()

		if thread.is_alive():
			logger.info("Command %s will now be terminated because of timeout" % command)
			self.process.terminate()  # TODO or should it be killed?
			thread.join()
			logger.info("Command %s has been terminated" % command)
			self.feedbacksender.send({"status": "error", "errormessage": "Stopped by timeout", "errorcode": 732}, finished=True)

		# TODO, check if the process has crashed, and give exitstatus: crashed
		else:
			logger.info("Command %s execution completed ok. Exitcode %d" % (command, self.process.returncode))
			if self.process.returncode is 0:
				self.feedbacksender.send({"status": "finished", "exitstatus": "normal_exit",
					 "exitcode": self.process.returncode}, finished=True)
			else:
				self.feedbacksender.send({"status": "error", "errorcode": self.errorprefix + str(self.process.returncode), "errormessage": self.errorprefix + str(self.process.returncode)}, finished=True)

		return self.process.returncode

	def readandsend(self):
		# TODO: check that below code works OK with vup stdout encoding (UTF-8), including non-standard ASCII chars

		while True:
			self.process.stdout.flush()
			line = self.process.stdout.readline()
			# Max length on pubnub is 1800 chars, and output is much better readable with the bare eye
			# when sent per line. So no need to send it alltogether.
			self.feedbacksender.send({"status": "running", "xmloutput": line})
			if line == '' and self.process.poll() != None:
				break
			sleep(0.1)
