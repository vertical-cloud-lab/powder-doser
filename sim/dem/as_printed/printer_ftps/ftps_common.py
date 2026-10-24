# Runs on the Pi (exec'd from stdin). `ip` and `code` are provided by the wrapper and are never printed.
import ftplib, socket, ssl, sys, time

class ImplicitFTP_TLS(ftplib.FTP_TLS):
    def connect(self, host="", port=0, timeout=-999, source_address=None):
        if host: self.host = host
        if port: self.port = port
        if timeout != -999: self.timeout = timeout
        if source_address is not None: self.source_address = source_address
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.af = self.sock.family
        self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
        return conn, size

def open_ftps():
    ctx = ssl._create_unverified_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    f = ImplicitFTP_TLS(context=ctx)
    f.connect(ip, 990, 30)
    f.login("bblp", code)
    f.prot_p()
    return f
