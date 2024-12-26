from aiogram import Dispatcher
from .router_pro9 import router as router_pro9
from .router_zhizn import router as router_zhizn

def setup_routers(token, dp: Dispatcher):
    if token == 'TOKEN_PRO9':
        dp.include_router(router_pro9)
    if token == 'TOKEN_ZHIZN':
        dp.include_router(router_zhizn)