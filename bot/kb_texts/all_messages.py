import datetime

no_wallet = """Oops! Seems like you haven't configured your ETH wallet yet. 🚨\nBefore you start splashing in the token market or executing transactions, it's essential to have your ETH wallet in place. 🛠️\nEager to dive in? Set up your wallet now and let's get started! 🚀🌊"""
home_message = '''🎯 Welcome to 0xs Sniper Bot! 🎯\n\nHey there, Sniper! 🕵️‍♀️\n\nIf you're on the hunt for the best crypto deals and the fastest trading opportunities, you're in the right place. With 0xs Sniper, you get the edge you need to snipe tokens, manage your ETH wallet, and navigate the DeFi landscape like a pro.\n\n📈 **Features**:\n- 🔥 Real-time token sniping\n- 🛠️ Wallet management\n- 💸 Quick transaction execution\n\nReady to level up your crypto game? Let's get sniping! 🚀'''
no_open_trades = "🔍 **Status Check**: Looks like the coast is clear – no ongoing trades at the moment! 🌌"
trade_sell_conf = "🤔 **Final Call**: Are you sure you want to liquidate this trade? 💸📉"
sell_all_conf = "🤔 **Double Check**: Are you absolutely sure you want to exit all trades? 🚀📉"


def get_new_wallet_mesg(wallet_name, network, wallet, private, seed):
    message = f'''🔐 **Wallet Successfully Generated!**
🏷️ **Wallet Label**: {wallet_name}
🌐 **Blockchain**: {network}
📭 **Public Address**: `{wallet}`
🗝️ **PrivKey**: `{private}`
📜 **Seed Words**: `{seed}`

🚨 **SECURITY CAUTIONS** 🚨
1️⃣ Record your mnemonic phrase OR private key using **ink and paper ONLY**.
2️⃣ Evade digital footprints. **NEVER** snapshot or duplicate digitally.
3️⃣ Compatible with Metamask/Trust Wallet for import.
4️⃣ **Erase this message** post documentation.
⚠️ This bot won't replicate this data for your security. Safeguard your funds! 🛡️'''
    return message



def get_trade_message(trade, coin_price, pnl, balance, eth_liq, token_liq):
    emoji = "🟢" if pnl >= 0 else "🔴"
    pnl_percentage = pnl * 100

    # Calculate the age of the trade
    now = datetime.datetime.now()
    trade_age = now - trade.timestamp
    trade_age_str = str(trade_age).split(".")[0]  # Remove microseconds

    message = (
    f"🚀 **Exploring** {trade.coin_name} ({trade.coin_symbol}) 🌌\n\n"
    f"{emoji} **P&L Overview**: {pnl:.2f} ({pnl_percentage:.2f}%)\n"
    f"📈 **Current Market Price**: {coin_price:.18f}\n"
    f"🎯 **Acquired At**: {trade.price_in}\n"
    f"🔗 **Trading Platform**: {trade.coin_dex}\n"
    f"💼 **Your Portfolio**: {balance}\n"
    f"⏳ **Duration of Trade**: {trade_age_str}\n\n"
    f"🌐 **WETH Liquidity**: {eth_liq}\n"
    f"💦 **{trade.coin_symbol} Reservoir**: {token_liq}\n\n"
    f"🛠️ Take further actions below!"
        )

    return message