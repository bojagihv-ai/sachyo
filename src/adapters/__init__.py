from src.adapters.auction import AuctionAdapter
from src.adapters.coupang import CoupangAdapter
from src.adapters.demo import DemoAdapter
from src.adapters.elevenst import ElevenStAdapter
from src.adapters.gmarket import GmarketAdapter
from src.adapters.interpark import InterparkAdapter
from src.adapters.lotteon import LotteOnAdapter
from src.adapters.naver_smartstore import NaverSmartstoreAdapter
from src.adapters.ssg import SsgAdapter
from src.adapters.tmon import TmonAdapter
from src.adapters.wemakeprice import WemakepriceAdapter


def build_adapters(source_names: list[str], max_candidates: int):
    mapping = {
        "demo": DemoAdapter,
        "coupang": CoupangAdapter,
        "naver": NaverSmartstoreAdapter,
        "smartstore": NaverSmartstoreAdapter,
        "11st": ElevenStAdapter,
        "gmarket": GmarketAdapter,
        "auction": AuctionAdapter,
        "ssg": SsgAdapter,
        "lotteon": LotteOnAdapter,
        "wemakeprice": WemakepriceAdapter,
        "tmon": TmonAdapter,
        "interpark": InterparkAdapter,
    }
    adapters = []
    unsupported = []
    for s in source_names:
        cls = mapping.get(s)
        if cls is None:
            unsupported.append(s)
            continue
        adapters.append(cls(max_candidates=max_candidates))
    return adapters, unsupported
