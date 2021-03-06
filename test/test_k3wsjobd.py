#!/usr/bin/env python
# coding: utf-8

import os
import random
import time
import unittest

import websocket

import k3proc
import k3utfjson
import k3ut
from k3wsjobd import Job
from k3wsjobd.test.wsjobd_server import PORT

dd = k3ut.dd

random.seed(time.time())
this_base = os.path.dirname(__file__)


def subproc(script, env=None):
    if env is None:
        env = dict(PYTHONPATH=this_base + '/../..', )

    return k3proc.shell_script(script, env=env)


class TestWsjobd(unittest.TestCase):

    @classmethod
    def _clean(cls):
        try:
            subproc('python {b}/wsjobd_server.py stop'.format(b=this_base))
        except Exception as e:
            dd('failed to stop wsjobd server: ' + repr(e))

        time.sleep(0.1)

    @classmethod
    def setUpClass(cls):
        cls._clean()
        subproc('python {b}/wsjobd_server.py start'.format(b=this_base))
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls._clean()

    def _create_client(self):
        ws = websocket.WebSocket()
        ws.connect('ws://127.0.0.1:%d' % PORT)
        ws.timeout = 6
        return ws

    def setUp(self):
        self.ws = self._create_client()

    def tearDown(self):
        self.ws.close()

    def get_random_ident(self):
        return 'random_ident_%d' % random.randint(10000, 99999)

    def _wait_for_result(self, ws):
        # wait for test_job_echo.run to fillin resp['result']
        for _ in range(3):
            resp = k3utfjson.load(ws.recv())
            if 'result' in resp:
                break
            time.sleep(0.1)
        return resp

    def test_invalid_jobdesc(self):
        cases = (
            ('foo', 'not json'),
            (k3utfjson.dump('foo'), 'not dict'),
            (k3utfjson.dump({}), 'no func'),
            (k3utfjson.dump({'func': 'foo'}), 'no ident'),
            (k3utfjson.dump({'ident': 'bar'}), 'no func'),
            (k3utfjson.dump({'ident': 'bar', 'func': {}}), 'invalid func'),
            (k3utfjson.dump({'ident': 44, 'func': 'foo'}), 'invalid ident'),
            (k3utfjson.dump({'ident': 'foo', 'func': 'foo', 'jobs_dir': {}}),
             'invalid jobs_dir'),
        )
        for msg, desc in cases:
            ws = self._create_client()
            ws.send(msg)
            resp = k3utfjson.load(ws.recv())
            self.assertIn('err', resp, desc)
            ws.close()

    def test_normal_job(self):
        job_desc = {
            'func': 'test_job_normal.run',
            'ident': self.get_random_ident(),
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self._wait_for_result(self.ws)
        dd(resp)
        self.assertEqual('foo', resp['result'], 'test get result')

    def test_report_interval(self):
        job_desc = {
            'func': 'test_job_loop_10.run',
            'ident': self.get_random_ident(),
            'progress': {
                'interval': 0.5,
            },
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        self.ws.recv()
        first_report_time = time.time()

        self.ws.recv()
        second_report_time = time.time()

        actual_interval = second_report_time - first_report_time

        diff = actual_interval - job_desc['progress']['interval']

        # tolerate 0.1 second of difference
        self.assertLess(diff, 0.1)

    def test_invalid_progress_key(self):
        job_desc = {
            'func': 'test_job_progress_key.run',
            'ident': self.get_random_ident(),
            'progress': {
                'key': 'inexistent',
            },
            'report_system_load': True,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self.ws.recv()
        dd(repr(resp))
        resp = k3utfjson.load(resp)
        self.assertIsNone(resp)

    def test_progress_key(self):
        job_desc = {
            'func': 'test_job_progress_key.run',
            'ident': self.get_random_ident(),
            'progress': {
                'key': 'foo',
            },
            # progress_sender may try to read data["foo"] before job starts.
            # need to preset a value.
            "foo": "0%",
            'report_system_load': True,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self.ws.recv()
        dd(repr(resp))
        resp = k3utfjson.load(resp)
        # progress may be set by job runner or job desc
        self.assertIn(resp, ('80%', '0%'))

    def test_check_system_load(self):
        job_desc = {
            'func': 'test_job_normal.run',
            'ident': self.get_random_ident(),
            'check_load': {
                'mem_low_threshold': 100 * 1024 ** 3,
                'cpu_low_threshold': 0,
            },
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self.ws.recv()
        resp = k3utfjson.load(resp)
        self.assertEqual('SystemOverloadError', resp['err'])

        job_desc = {
            'func': 'test_job_normal.run',
            'ident': self.get_random_ident(),
            'check_load': {
                'cpu_low_threshold': 100.1,
                'mem_low_threshold': 0,
            },
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        ws2 = self._create_client()
        ws2.send(k3utfjson.dump(job_desc))

        resp = ws2.recv()
        resp = k3utfjson.load(resp)
        ws2.close()
        self.assertEqual('SystemOverloadError', resp['err'])

    def test_max_client_number(self):
        job_desc = {
            'func': 'test_job_loop_10.run',
            'ident': self.get_random_ident(),
            'check_load': {
                'max_client_number': 1,
                'cpu_low_threshold': 0,
                'mem_low_threshold': 0,
            },
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self.ws.recv()
        resp = k3utfjson.load(resp)
        self.assertNotIn('err', resp)

        job_desc = {
            'func': 'test_job_loop_10.run',
            'ident': self.get_random_ident(),
            'check_load': {
                'max_client_number': 1,
                'cpu_low_threshold': 0,
                'mem_low_threshold': 0,
            },
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        ws2 = self._create_client()
        ws2.send(k3utfjson.dump(job_desc))

        resp = ws2.recv()
        resp = k3utfjson.load(resp)
        self.assertEqual('SystemOverloadError', resp['err'])
        ws2.close()

    def test_module_not_exists(self):
        job_desc = {
            'func': 'foo.bar',
            'ident': self.get_random_ident(),
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = k3utfjson.load(self.ws.recv())
        self.assertIn('err', resp)

    def test_report_system_load(self):
        job_desc = {
            'func': 'test_job_normal.run',
            'ident': self.get_random_ident(),
            'report_system_load': True,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = k3utfjson.load(self.ws.recv())
        self.assertIn('mem_available', resp['system_load'])
        self.assertIn('cpu_idle_percent', resp['system_load'])
        self.assertIn('client_number', resp['system_load'])

    def test_same_ident_same_job(self):
        ident = self.get_random_ident()
        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'foo',
            'sleep_time': 10,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = k3utfjson.load(self.ws.recv())
        self.assertEqual('foo', resp['result'])

        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'bar',
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        ws = self._create_client()
        ws.send(k3utfjson.dump(job_desc))

        resp = k3utfjson.load(ws.recv())
        ws.close()
        # not bar, because the ident is same as the first job,
        # if job exists, it will not create a new one
        self.assertEqual('foo', resp['result'])
        self.assertEqual('foo', resp['echo'])

    def test_same_ident_different_job(self):
        ident = self.get_random_ident()
        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'foo',
            'sleep_time': 0.1,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self._wait_for_result(self.ws)
        self.assertEqual('foo', resp['result'])

        time.sleep(0.2)

        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'bar',
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        ws2 = self._create_client()
        ws2.send(k3utfjson.dump(job_desc))

        resp = self._wait_for_result(ws2)
        ws2.close()
        # old job with the same ident has exit, it will create a new one
        self.assertEqual('bar', resp['result'])
        self.assertEqual('bar', resp['echo'])

    def test_client_close(self):
        ident = self.get_random_ident()
        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'foo',
            'time_sleep': 10,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))
        self.ws.close()
        self.ws = self._create_client()

        job_desc = {
            'func': 'test_job_echo.run',
            'ident': ident,
            'echo': 'bar',
            'time_sleep': 10,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = self.ws.recv()
        resp = k3utfjson.load(resp)
        self.assertEqual('foo', resp['result'])

    def test_invalid_cpu_sample_interval(self):
        job_desc = {
            'func': 'test_job_normal.run',
            'ident': self.get_random_ident(),
            'cpu_sample_interval': 'foo',
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))

        resp = k3utfjson.load(self.ws.recv())
        self.assertEqual('InvalidMessageError', resp['err'])

    def test_invalid_check_load_args(self):
        cases = (
            {'check_load': {'mem_low_threshold': 'foo',
                            'cpu_low_threshold': 0}},
            {'check_load': {'cpu_low_threshold': None,
                            'mem_low_threshold': 0}},
            {'check_load': {'max_client_number': {},
                            'cpu_low_threshold': 0,
                            'mem_low_threshold': 0}},
        )

        job_desc = {
            'func': 'test_job_normal.run',
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        for case in cases:
            case.update(job_desc)
            case['ident'] = self.get_random_ident()

            ws = self._create_client()
            ws.send(k3utfjson.dump(case))

            resp = k3utfjson.load(ws.recv())
            ws.close()
            self.assertEqual('InvalidMessageError', resp['err'])

    def test_func_not_exists(self):
        ident = self.get_random_ident()
        job_desc = {
            'func': 'test_job_echo.func_not_exists',
            'ident': ident,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
        }

        self.ws.send(k3utfjson.dump(job_desc))
        resp = self.ws.recv()
        resp = k3utfjson.load(resp)
        self.assertEqual('LoadingError', resp['err'])

    def test_worker_exception(self):
        ident = self.get_random_ident()
        job_desc = {
            'func': 'test_job_worker_exception.run',
            'ident': ident,
            'jobs_dir': 'k3wsjobd/test/test_jobs',
            'progress': {
                'interval': 0.1,
            },
        }

        self.ws.send(k3utfjson.dump(job_desc))

        for i in range(10):
            resp = self.ws.recv()
            self.assertNotIn('err', resp)

        with self.assertRaises(Exception):
            for i in range(3):
                self.ws.recv()

    def test_create_job(self):
        self.assertEqual(0, len(Job.sessions))

        def f(self):
            time.sleep(0.2)
            return

        Job('channel', {'ident': 'a'}, f)
        joba = Job.sessions['a']

        self.assertEqual(1, len(Job.sessions))

        Job('channel', {'ident': 'a'}, f)
        joba1 = Job.sessions['a']

        #  joba already exists
        self.assertEqual(joba1, joba)
        self.assertEqual(1, len(Job.sessions))

        time.sleep(0.15)
        Job('channel', {'ident': 'b'}, f)

        self.assertEqual(2, len(Job.sessions))

        time.sleep(0.15)
        self.assertEqual(1, len(Job.sessions))

        time.sleep(0.1)
        self.assertEqual(0, len(Job.sessions))

        #  test use same ident after first one exit
        Job('channel', {'ident': 'a'}, f)
        joba1 = Job.sessions['a']

        time.sleep(0.25)

        Job('channel', {'ident': 'a'}, f)
        joba2 = Job.sessions['a']
        self.assertNotEqual(joba1, joba2)
