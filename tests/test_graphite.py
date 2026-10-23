import importlib.util
import pathlib
import queue
import socket
import threading

import graphite


def test_installer_loads_on_weewx5():
    path = pathlib.Path(__file__).resolve().parents[1] / 'install.py'
    spec = importlib.util.spec_from_file_location('graphite_install', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    installer = module.loader()
    assert installer['restful_services'] == 'user.graphite.Graphite'


def test_carbon_wire_has_original_epoch_and_skips_missing():
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(8)
    listener.settimeout(2)
    received = []

    def receive():
        while True:
            try:
                connection, _ = listener.accept()
            except (TimeoutError, OSError):
                return
            with connection:
                received.append(connection.makefile('rb').read())

    server = threading.Thread(target=receive)
    server.start()
    try:
        worker = graphite.GraphiteThread(queue.Queue(), None, host='127.0.0.1', port=str(listener.getsockname()[1]), timeout=1)
        worker.process_record({'dateTime':1700000000, 'outTemp':0, 'windDir':None}, None)
        server.join(3)
        lines = b''.join(received).decode().splitlines()
        assert 'weewx.outTemp 0.000000 1700000000' in lines
        assert not any('windDir' in line for line in lines)
    finally:
        listener.close()
        server.join(3)


def test_service_initializes_with_current_config_api(monkeypatch,tmp_path):
    import configobj
    import weewx
    events=[]

    class Engine:
        def bind(self,*args):
            events.append(args)

    config=configobj.ConfigObj({'StdRESTful':{'Graphite':{'host':'localhost','port':'2003'}},'DataBindings':{'wx_binding':{'database':'archive_sqlite'}},'Databases':{'archive_sqlite':{'driver':'weedb.sqlite','root':str(tmp_path),'database_name':'archive.sdb'}}})
    monkeypatch.setattr(graphite.GraphiteThread,'start',lambda self:None)
    service=graphite.Graphite(Engine(),config)
    assert service.archive_thread.host=='localhost'
    assert events[0][0]==weewx.NEW_ARCHIVE_RECORD


def start_service(monkeypatch, tmp_path, options):
    import configobj
    logged = []

    class Engine:
        def bind(self, *args):
            pass

    config = configobj.ConfigObj({'StdRESTful': {'Graphite': options}, 'DataBindings': {'wx_binding': {'database': 'archive_sqlite'}}, 'Databases': {'archive_sqlite': {'driver': 'weedb.sqlite', 'root': str(tmp_path), 'database_name': 'archive.sdb'}}})
    monkeypatch.setattr(graphite.GraphiteThread, 'start', lambda self: None)
    monkeypatch.setattr(graphite.syslog, 'syslog', lambda level, message: logged.append((level, message)))
    return graphite.Graphite(Engine(), config), logged


def test_missing_port_is_logged_and_skips_uploader(monkeypatch, tmp_path):
    service, logged = start_service(monkeypatch, tmp_path, {'host': 'localhost'})
    assert not hasattr(service, 'archive_thread')
    assert (graphite.syslog.LOG_ERR, 'restx: Graphite: Data will not be posted: Missing option port') in logged


def test_unknown_options_are_logged_and_ignored(monkeypatch, tmp_path):
    service, logged = start_service(monkeypatch, tmp_path, {'host': 'localhost', 'port': '2003', 'enable': 'true', 'post_intervall': '60'})
    assert service.archive_thread.host == 'localhost'
    assert (graphite.syslog.LOG_WARNING, "restx: Graphite: Unknown option 'post_intervall' ignored") in logged


def test_unreachable_receiver_is_retried_and_thread_keeps_running(monkeypatch):
    attempts = []
    sleeps = []

    def refuse(address, timeout):
        attempts.append(address)
        raise ConnectionRefusedError(111, 'Connection refused')

    monkeypatch.setattr(graphite.socket, 'create_connection', refuse)
    monkeypatch.setattr(graphite.time, 'sleep', sleeps.append)
    records = queue.Queue()
    worker = graphite.GraphiteThread(records, None, host='127.0.0.1', port='2003', post_interval=0, max_tries=2, retry_wait=7)
    records.put({'dateTime': 1700000000, 'outTemp': 0})
    records.put(None)
    # run_loop() returns at the None record unless an exception ends the thread.
    worker.run_loop()
    assert len(attempts) == 2
    assert sleeps == [7]
