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
