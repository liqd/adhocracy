"""
Helper module for captchas from captchas.net
"""

from adhocracy import config
from adhocracy.lib.captchasdotnet import CaptchasDotNet


def get_captchasdotnet():
    return CaptchasDotNet(
        client=config.get('captchasdotnet.user_name'),
        secret=config.get('captchasdotnet.secret'),
        alphabet=config.get('captchasdotnet.alphabet'),
        letters=config.get_int('captchasdotnet.letters'),
        width=240,
        height=80,
        random_repository=config.get('captchasdotnet.random_repository'),
        cleanup_time=3600
    )
