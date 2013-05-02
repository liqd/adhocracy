from adhocracy.tests import TestController
from adhocracy.lib.session import Session

# Use the PlainValueConverter to make it easier to test the session
from adhocracy.lib.session.converter import PlainValueConverter


class SessionTestController(TestController):
    _domain = "adhocracy.lan"
    _test_string = "\"'Perry' Rhodan\"☃⁋"
    _test_encoded = "\\\"\\'Perry\\' Rhodan\\\"\x2603\x204b"
    _test_cookie_value = "President={0}; Domain=.adhocracy.lan".format(
            self._test_cookie_value)
    _test_cookie_header = "Set-Cookie: {0}".format(self._test_cookie_value)

    def _config(self, **add_config):
        config = {}

        config["adhocracy.domain"] = self._domain

        config.update(add_config)
        return config

    def _environ(self, **add_environ):
        environ = {}

        environ["HTTP_COOKIE"] = "Cookie: {0}".format(self._test_cookie_value)

        environ.update(add_environ)
        return environ

    def session_with_no_extra_config(self):
        session = Session({}, self._config(),
                value_converter=PlainValueConverter)

        session["President"] = self._test_string

        # Check that we get what we put into
        self.assertEqual(session["President"], self._test_string)

        # Check that it produces the correct `Set-Cookie` header
        self.assertEqual(session._cookie["President"], self._test_cookie_header)

        if "path_check" in add_tests:
            self.assertTrue("Path=/test" in session._cookie["President"])

        if "http_only_check" in add_tests:
            self.assertTrue("HttpOnly" in session._cookie["President"])

    def session_with_path(self):
        session = Session({}, self._config(), path="/test",
                value_converter=PlainValueConverter)

        session["President"] = self._test_string

        # Check that we get what we put into
        self.assertEqual(session["President"], self._test_string)

        # Check that it produces the correct `Set-Cookie` header
        self.assertEqual(session._cookie["President"], self._test_cookie_header)

        if "path_check" in add_tests:
            self.assertTrue("Path=/test" in session._cookie["President"])

        if "http_only_check" in add_tests:
            self.assertTrue("HttpOnly" in session._cookie["President"])

    def session_with_http_only(self):
        session = Session({}, self._config(), http_only=True,
                value_converter=PlainValueConverter)

        session["President"] = self._test_string

        # Check that we get what we put into
        self.assertEqual(session["President"], self._test_string)

        # Check that it produces the correct `Set-Cookie` header
        self.assertEqual(session._cookie["President"], self._test_cookie_header)

        if "path_check" in add_tests:
            self.assertTrue("Path=/test" in session._cookie["President"])

        if "http_only_check" in add_tests:
            self.assertTrue("HttpOnly" in session._cookie["President"])

    def session_with_path_and_http_only(self):
        session = Session({}, self._config(), path="/test", http_only=True,
                value_converter=PlainValueConverter)

        session["President"] = self._test_string

        # Check that we get what we put into
        self.assertEqual(session["President"], self._test_string)

        # Check that it produces the correct `Set-Cookie` header
        self.assertEqual(session._cookie["President"], self._test_cookie_header)

        if "path_check" in add_tests:
            self.assertTrue("Path=/test" in session._cookie["President"])

        if "http_only_check" in add_tests:
            self.assertTrue("HttpOnly" in session._cookie["President"])


    def session_load_from_cookie(self):
        session = Session(self._environ(), self._config(),
                value_converter=PlainValueConverter)

        session["President"] = self._test_string

        # Check that we get what we put into
        self.assertEqual(session["President"], self._test_string)

        # Check that it produces the correct `Set-Cookie` header
        self.assertEqual(session._cookie["President"], self._test_cookie_header)

        if "path_check" in add_tests:
            self.assertTrue("Path=/test" in session._cookie["President"])

        if "http_only_check" in add_tests:
            self.assertTrue("HttpOnly" in session._cookie["President"])


