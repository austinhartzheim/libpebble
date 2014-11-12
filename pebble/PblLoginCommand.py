from PblAccount import PblAccount, get_default_account
from PblCommand import PblCommand

class PblLoginCommand(PblCommand):
    name = 'login'
    help = ""

    def run(self, args):
        account = get_default_account()
        account.login()
