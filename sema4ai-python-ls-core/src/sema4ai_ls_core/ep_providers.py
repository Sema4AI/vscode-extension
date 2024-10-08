import sys

from sema4ai_ls_core.protocols import IConfig, IDirCache, IEndPoint

if sys.version_info[:2] < (3, 8):

    class Protocol:
        pass

else:
    from typing import Protocol


# ===============================================================================
# EPConfigurationProvider
# ===============================================================================
class EPConfigurationProvider(Protocol):
    @property
    def config(self) -> IConfig:
        pass


class DefaultConfigurationProvider:
    def __init__(self, config: IConfig):
        self.config = config


# ===============================================================================
# EPDirCacheProvider
# ===============================================================================
class EPDirCacheProvider(Protocol):
    @property
    def dir_cache(self) -> IDirCache:
        pass


class DefaultDirCacheProvider:
    def __init__(self, dir_cache: IDirCache):
        self.dir_cache = dir_cache


# ===============================================================================
# EPEndPointProvider
# ===============================================================================
class EPEndPointProvider(Protocol):
    @property
    def endpoint(self) -> IEndPoint:
        pass


class DefaultEndPointProvider:
    def __init__(self, endpoint: IEndPoint):
        self.endpoint = endpoint
