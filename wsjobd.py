#!/usr/bin/env python
# coding: utf-8

import logging
import threading
from collections import OrderedDict

import psutil
from geventwebsocket import Resource
from geventwebsocket import WebSocketApplication
from geventwebsocket import WebSocketError
from geventwebsocket import WebSocketServer

import k3thread
import k3utfjson
import k3jobq

logger = logging.getLogger(__name__)

MEM_AVAILABLE = "mem_available"
CPU_IDLE_PERCENT = "cpu_idle_percent"
CLIENT_NUMBER = "client_number"
JOBS_DIR = "jobs"

# - `mem_low_threshold`
# set the min size of available memory the system should have, if not satified, return error. the default is 500M
#
# - `cpu_low_threshold`
# set the min idle percent of the system cpu, if not satified, return error. the default is 3
#
# - `max_client_number`
# set the max client number, if this number reached, new connection will be refused. the default is 1000


CHECK_LOAD_PARAMS = {
    "mem_low_threshold": {
        "load_name": MEM_AVAILABLE,
        "default": 500 * 1024**2,  # 500M
        "greater": True,
    },
    "cpu_low_threshold": {
        "load_name": CPU_IDLE_PERCENT,
        "default": 3,  # 3%
        "greater": True,
    },
    "max_client_number": {
        "load_name": CLIENT_NUMBER,
        "default": 1000,
        "greater": False,
    },
}


class SystemOverloadError(Exception):
    pass


class JobError(Exception):
    pass


class InvalidMessageError(JobError):
    pass


class InvalidProgressError(InvalidMessageError):
    pass


class LoadingError(JobError):
    pass


class JobNotInSessionError(JobError):
    pass


class Job(object):
    lock = threading.RLock()
    sessions = {}

    def __init__(self, channel, msg, func):
        """
        Job description is a string formatted in json, it is used to tell wsjobd what to do,
         it can contain the following fields:
        :param channel:
        report_system_load: a boolean to indicate whether to report system load, if set to true and the progress info
        is a dict, then the system load info will be add to progress dict by key `system_load`, the value is also a dict
        , which contains three fields: `mem_available`, `cpu_idle_percent`, `client_number`.
        cpu_sample_interval: set the interval used by psutil.cpu_times_percent, the default is 0.02
        :param msg:
        check_load: a dict to enable system load check, also to set customed thresholds, the can contain the following fields
        ident : required. the identifier of a job, it is used to prevent from creating the same job repeatedly.
        progress: a dict to set progress reporting related settings, it can contain the following fields:
            - `interval`: the interval of progress reporting, default is 5 seconds
        `key`: the sub field in which the progress info located
        :param func: required. the function of job, it contain module name and function name, seperated by a dot,
        the module shoud in the `jobs` directory.
        """
        self.ident = msg["ident"]
        self.channel = channel
        self.data = msg
        self.worker = func
        self.ctx = {}
        self.err = None
        self.progress_available = threading.Event()

        if self.ident in self.sessions:
            logger.info(
                "job: %s already exists, created by chennel %s" % (self.ident, repr(self.sessions[self.ident].channel))
            )
            return
        else:
            self.sessions[self.ident] = self
            logger.info(
                ("inserted job: %s to sessions by channel %s, " + "there are %d jobs in sessions now")
                % (self.ident, repr(self.channel), len(self.sessions))
            )

        self.thread = k3thread.start(target=self.work, args=(), daemon=True)

    def work(self):
        logger.info("job %s started, the data is: %s" % (self.ident, self.data))

        try:
            self.worker(self)
        except Exception as e:
            logger.exception("job %s got exception: %s" % (self.ident, repr(e)))
            self.err = e
        finally:
            logger.info("job %s ended" % self.ident)
            self.close()

    def close(self):
        with self.lock:
            del self.sessions[self.ident]
            logger.info(
                ("removed job: %s from sessions, there are %d " + "jobs in sessions now")
                % (self.ident, len(self.sessions))
            )


def get_or_create_job(channel, msg, func):
    with Job.lock:
        Job(channel, msg, func)

        job = Job.sessions.get(msg["ident"])

    return job


def progress_sender(job, channel, interval=5, stat=None):
    stat = stat or (lambda data: data)
    data = job.data

    i = 10
    try:
        while True:
            # if thread died due to some reason, still send 10 stats
            if not job.thread.is_alive():
                logger.info("job %s died: %s" % (job.ident, repr(job.err)))
                if i == 0:
                    channel.ws.close()
                    break
                i -= 1

            logger.info("jod %s on channel %s send progress: %s" % (job.ident, repr(channel), repr(stat(data))))

            to_send = stat(data)
            if channel.report_system_load and isinstance(to_send, dict):
                to_send["system_load"] = channel.get_system_load()

            channel.ws.send(k3utfjson.dump(to_send))

            if job.progress_available.wait(interval):
                job.progress_available.clear()

    except WebSocketError as e:
        if channel.ws.closed:
            logger.info("the client has closed the connection")
        else:
            logger.exception(
                ("got websocket error when sending progress on" + " channel %s: %s") % (repr(channel), repr(e))
            )

    except Exception as e:
        logger.exception("got exception when sending progress on channel %s: %s" % (repr(channel), repr(e)))
        channel.ws.close()


class JobdWebSocketApplication(WebSocketApplication):
    jobq_mgr = None

    def on_open(self):
        logger.info("on open, the channel is: " + repr(self))
        self.ignore_message = False

    def _parse_request(self, message):
        try:
            try:
                msg = k3utfjson.load(message)
            except Exception:
                raise InvalidMessageError("message is not a vaild json string: %s" % message)

            self._check_msg(msg)

            self.report_system_load = msg.get("report_system_load") is True
            self.cpu_sample_interval = msg.get("cpu_sample_interval", 0.02)

            if not isinstance(self.cpu_sample_interval, (int, float)):
                raise InvalidMessageError("cpu_sample_interval is not a number")

            check_load = msg.get("check_load")
            if isinstance(check_load, dict):
                self._check_system_load(check_load)

            self.jobs_dir = msg.get("jobs_dir", JOBS_DIR)

            self._setup_response(msg)
            return

        except SystemOverloadError as e:
            logger.info("system overload on chennel %s, %s" % (repr(self), repr(e)))
            self._send_err_and_close(e)

        except JobError as e:
            logger.info("error on channel %s while handling message, %s" % (repr(self), repr(e)))
            self._send_err_and_close(e)

        except Exception as e:
            logger.exception(("exception on channel %s while handling " + "message, %s") % (repr(self), repr(e)))
            self._send_err_and_close(e)

    def on_message(self, message):
        logger.info("on message, the channel is: %s, the message is: %s" % (repr(self), message))
        if self.ignore_message:
            return

        else:
            self.ignore_message = True

        self.jobq_mgr.put((self, message))

    def _send_err_and_close(self, err):
        try:
            err_msg = {
                "err": err.__class__.__name__,
                "val": err.args,
            }
            self.ws.send(k3utfjson.dump(err_msg))
        except Exception as e:
            logger.error(("error on channel %s while sending back error " + "message, %s") % (repr(self), repr(e)))

    def get_system_load(self):
        return {
            MEM_AVAILABLE: psutil.virtual_memory().available,
            CPU_IDLE_PERCENT: psutil.cpu_times_percent(self.cpu_sample_interval).idle,
            CLIENT_NUMBER: len(self.protocol.server.clients),
        }

    def _check_system_load(self, check_load):
        system_load = self.get_system_load()

        for param_name, param_attr in CHECK_LOAD_PARAMS.items():
            param_value = check_load.get(param_name, param_attr["default"])

            if not isinstance(param_value, (int, float)):
                raise InvalidMessageError("%s is not a number" % param_name)

            load_name = param_attr["load_name"]
            diff = system_load[load_name] - param_value

            if not param_attr["greater"]:
                diff = 0 - diff

            if diff < 0:
                raise SystemOverloadError(
                    "%s: %d is %s than: %d"
                    % (load_name, system_load[load_name], param_attr["greater"] and "less" or "greater", param_value)
                )

    def _check_msg(self, msg):
        if not isinstance(msg, dict):
            raise InvalidMessageError("message is not dictionary")

        if "ident" not in msg:
            raise InvalidMessageError("'ident' is not in message")

        if "func" not in msg:
            raise InvalidMessageError("'func' is not in message")

    def _setup_response(self, msg):
        func = self._get_func_by_name(msg)
        channel = self
        job = get_or_create_job(channel, msg, func)

        if job is None:
            raise JobNotInSessionError("job not in sessions: " + repr(Job.sessions))

        progress = msg.get("progress", {})

        if progress in (None, False):
            return

        if not isinstance(progress, dict):
            raise InvalidProgressError("the progress in message is not a dictionary")

        interval = progress.get("interval", 5)
        progress_key = progress.get("key")

        def get_progress(r):
            if progress_key is None:
                return r
            return r.get(progress_key)

        k3thread.start(target=progress_sender, args=(job, channel, interval, get_progress), daemon=True)

    def _get_func_by_name(self, msg):
        mod_func = self.jobs_dir.split("/") + msg["func"].split(".")
        mod_path = ".".join(mod_func[:-1])
        func_name = mod_func[-1]

        try:
            mod = __import__(mod_path)
        except (ImportError, SyntaxError) as e:
            raise LoadingError("failed to import %s: %s" % (mod_path, repr(e)))

        for mod_name in mod_path.split(".")[1:]:
            mod = getattr(mod, mod_name)

        logger.info("mod imported from: " + repr(mod.__file__))

        try:
            func = getattr(mod, func_name)
        except AttributeError:
            raise LoadingError("function not found: " + repr(func_name))

        return func

    def on_close(self, reason):
        logger.info("on close, the channel is: " + repr(self))


def _parse_request(args):
    app, msg = args
    app._parse_request(msg)


def run(ip="127.0.0.1", port=63482, jobq_thread_count=10):
    JobdWebSocketApplication.jobq_mgr = k3jobq.JobManager([(_parse_request, jobq_thread_count)])

    WebSocketServer(
        (ip, port),
        Resource(OrderedDict({"/": JobdWebSocketApplication})),
    ).serve_forever()
