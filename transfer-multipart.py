#!/usr/bin/env python3

from aiohttp import ClientSession, MultipartReader, hdrs, web
import json


class TransferMultipart():

    def __init__(self, urls, port, host, log_file=None):
        if not isinstance(urls, list):
            urls = [urls]
        self.urls = urls
        self.port = port
        self.host = host
        if log_file:
            self.logger = self._init_logger(log_file)
        else:
            self.logger = None

        self.app = web.Application()
        self.app.add_routes([web.post('/', self._respond_request)])

        web.run_app(app=self.app, port=self.port)
        self._log('Server started as host {} on port {}.'.format(
                self.host, self.port))

    def _init_logger(self, log_file):
        import logging

        logger = logging.getLogger('transfer_multipart_daemon')
        logger.setLevel(logging.INFO)

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(formatstr)
        fh.setFormatter(formatter)

        logger.addHandler(fh)

        return logger

    def _log(self, message, type='info'):
        if self.logger:
            if type == 'error':
                self.logger.error(message)
            elif type == 'warning':
                self.logger.warning(message)
            else:
                self.logger.info(message)

    async def _parse_request(self, resp):
        try:
            reader = MultipartReader.from_response(resp)
        except KeyError:
            self._log('Request is not of type multipart.', 'warning')
            return None
        else:
            self._log('Multipart request received.')

        # Loop through multipart data
        metadata = None
        while True:
            part = await reader.next()

            if part is None:
                break

            # Verify if part contains header
            try:
                content_type = part.headers[hdrs.CONTENT_TYPE]
            except KeyError:
                self._log('Parsed part did not contain content_type header.',
                          'warning')
                continue
            else:
                # Verify if part is of type JSON
                if content_type == 'application/json':
                    metadata = await part.json()
                    self._log('Parsed part of type JSON, stop parsing.')
                    break
                else:
                    self._log('Parsed part not of type JSON.', 'warning')

        return metadata

    async def _transfer_request(self, metadata):
        # Transfer pure JSON call to home-assistant
        async with ClientSession() as session:
            answers = []
            for url in self.urls:
                async with session.post(url, json=metadata) as resp:
                    self._log('Transfer request to {}.'.format(url))

                    answer = json.loads(await resp.text())[0]
                    if answer:
                        self._log('Received answer to transfer request.')
                        answers.append(answer)
                    else:
                        self._log('Received no answer to transfer request.',
                                  'warning')

        return answers

    async def _respond_request(self, resp):
        metadata = await self._parse_request(resp)

        # Abort if no metadata
        if not metadata:
            self._log('No data to transfer received.', 'error')
            raise web.HTTPBadRequest()

        answers = await self._transfer_request(metadata)

        # Abort if no answer from home-assistant received
        if not answers:
            self._log('No answer from transfer received.', 'error')
            return web.HTTPInternalServerError()

        self._log('Return answer from transfer request.')
        return web.Response(text=json.dumps(answers),
                            content_type='application/json')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description='Transfer and strip multipart JSON messages')
    parser.add_argument('-r', '--url', default='http://127.0.0.1:8123',
                        help='Remote target URL (multiple URLs separated by ' +
                             'comma possible)')
    parser.add_argument('-p', '--port', default=8321,
                        help='Local port to listen on')
    parser.add_argument('-l', '--host', default='http://0.0.0.0',
                        help='Local host address to listen on')
    parser.add_argument('--daemon', action='store_true', default=False,
                        help='Run script as daemon in background')
    parser.add_argument('--pid-file',
                        default='/var/run/transfer_multipart_daemon.pid',
                        help='Daemon PID file path')
    parser.add_argument('--log-file',
                        default=None,
                        help='Daemon LOG file path')
    args = parser.parse_args()
    urls = args.url.split(',')

    if args.daemon:
        import daemon
        from daemon.pidfile import TimeoutPIDLockFile

        with daemon.DaemonContext(pidfile=TimeoutPIDLockFile(args.pid_file)):
            TransferMultipart(urls, args.port, args.host, args.log_file)
    else:
        TransferMultipart(urls, args.port, args.host, args.log_file)
