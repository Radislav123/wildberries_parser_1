from django.core.management.commands import runserver
from core.management.commands import core_command


class Command(core_command.CoreCommand, runserver.Command):
    def on_bind(self, server_port):
        super().on_bind(server_port)

        if self._raw_ipv6:
            addr = f"[{self.addr}]"
        elif self.addr == "0":
            addr = "0.0.0.0"
        else:
            addr = self.addr

        print(f"Admin panel {self.protocol}://{addr}:{server_port}/admin/", file = self.stdout)
