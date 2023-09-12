import asyncio
from bot.snipers.sniper_v2_opt import SniperV2
from bot.snipers.sniper_v3 import SniperV3
from bot.listeners.uniswap_instant import UniswapListener

async def initialize_snipers():
    # Initialize SniperV2 classes
    # uniswap_v2_sniper = SniperV2("uniswap_v2")
    uniswap_listener = UniswapListener("uniswap_v2")
    # sushiswap_sniper = SniperV2("sushiswap")
  #  pancakeswap_v2_sniper = SniperV2("pancakeswap_v2")

    # Initialize SniperV3 classes
 #   uniswap_v3_sniper = SniperV3("uniswap_v3")
#    pancakeswap_v3_sniper = SniperV3("pancakeswap_v3")

    # Run the snipers concurrently
    await asyncio.gather(
        uniswap_listener.start_listening()
        # sushiswap_sniper.start_listening(),
    )
