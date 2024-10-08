# Original work Copyright 2018 Palantir Technologies, Inc. (MIT)
# See ThirdPartyNotices.txt in the project root for license information.
# All modifications Copyright (c) Robocorp Technologies Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http: // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import traceback


class JsonRpcException(Exception):
    def __init__(self, message=None, code=None, data=None):
        super().__init__(message)
        self.message = message or getattr(self.__class__, "MESSAGE")
        self.code = code or getattr(self.__class__, "CODE")
        self.data = data

    def to_dict(self):
        exception_dict = {"code": self.code, "message": self.message}
        if self.data is not None:
            exception_dict["data"] = self.data
        return exception_dict

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.code == other.code
            and self.message == other.message
        )

    def __hash__(self):
        return hash((self.code, self.message))

    @staticmethod
    def from_dict(error):
        for exc_class in _EXCEPTIONS:
            if exc_class.supports_code(error["code"]):
                return exc_class(**error)
        return JsonRpcException(**error)

    @classmethod
    def supports_code(cls, code):
        # Defaults to UnknownErrorCode
        return getattr(cls, "CODE", -32001) == code


class JsonRpcParseError(JsonRpcException):
    CODE = -32700
    MESSAGE = "Parse Error"


class JsonRpcInvalidRequest(JsonRpcException):
    CODE = -32600
    MESSAGE = "Invalid Request"


class JsonRpcMethodNotFound(JsonRpcException):
    CODE = -32601
    MESSAGE = "Method Not Found"

    @classmethod
    def of(cls, method):
        return cls(message=cls.MESSAGE + ": " + method)


class JsonRpcInvalidParams(JsonRpcException):
    CODE = -32602
    MESSAGE = "Invalid Params"


class JsonRpcInternalError(JsonRpcException):
    CODE = -32602
    MESSAGE = "Internal Error"

    @classmethod
    def of(cls, exc_info):
        exc_type, exc_value, exc_tb = exc_info
        return cls(
            message="".join(
                traceback.format_exception_only(exc_type, exc_value)
            ).strip(),
            data={"traceback": traceback.format_tb(exc_tb)},
        )


class JsonRpcRequestCancelled(JsonRpcException):
    CODE = -32800
    MESSAGE = "Request Cancelled"


class JsonRpcServerError(JsonRpcException):
    def __init__(self, message, code, data=None):
        assert _is_server_error_code(code)
        super().__init__(message=message, code=code, data=data)

    @classmethod
    def supports_code(cls, code):
        return _is_server_error_code(code)


def _is_server_error_code(code):
    return -32099 <= code <= -32000


_EXCEPTIONS = (
    JsonRpcParseError,
    JsonRpcInvalidRequest,
    JsonRpcMethodNotFound,
    JsonRpcInvalidParams,
    JsonRpcInternalError,
    JsonRpcRequestCancelled,
    JsonRpcServerError,
)
