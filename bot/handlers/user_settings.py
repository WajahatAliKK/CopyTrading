from aiogram import types , Router
from aiogram.fsm.context import FSMContext
from aiogram.types import ForceReply
import re

from bot.keyboards.settings_keyboard import user_settings_keyboard , addaddresskeyboard ,backbutton_to_setting
from bot.keyboards.paid_user_kb import paid_user_keyboard
from database.copytradingaddress import addcopytradingaddress  , deletecopyaddress , get_no_of_addresses , updateCopyTradePercentage , get_percentgae_of_copy_trade
from database.models import UserSetting , User 
from bot.states.sniperBot import UserSettingsState
from aiogram.types import  CallbackQuery
from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import selectinload 
from bot.db_client import db
from aiogram.filters.callback_data import CallbackData
from database.user_functions import get_user_by_chat_id, toggle_user_active
from database.user_settings_functions import get_user_settings, set_user_setting, add_user_settings
from aiogram.filters import StateFilter
from bot.utils.config import HOLDING_TOKEN_NAME, HOLDING_QUANTITY, ETH_FEE, GROUP_TITLE, default_arb_settings, default_bsc_settings, default_eth_settings
from bot.callback_factories.back import Back
from bot.callback_factories.start_action import StartAction
from bot.callback_factories.user_settings_action import UserSettingsAction
from bot.handlers.routers import user_settings_menu, wallet_menu
from aiogram import F
from bot.db_client import db
from aiogram.utils.keyboard import InlineKeyboardBuilder 

from bot.keyboards.menu_keyboard import ask_for_network, back_to_main_kb



# class for the start copy trade button 
class btnfortradecopy(CallbackData , prefix = 'call'):
    strt : str
    endno : int


@user_settings_menu.callback_query(StartAction.filter(F.type=="bot_active"), StateFilter("*"))
async def bot_active_cb(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    user = await get_user_by_chat_id(query.from_user.id, db)
    await toggle_user_active(user.id, db)
    user.is_active = not user.is_active
    kb = paid_user_keyboard(user)
    try:
        await query.message.edit_reply_markup(reply_markup=kb)
    except:
        message = "Bot state changed, may be due to restart on backend. Please go to main menu to proceed."
        await query.message.edit_text(text=message,reply_markup=back_to_main_kb())


def get_settings_message(setting):
    unit = "ETH"

    message = f'''
                🛠️ *Current Sniper Configurations*:

                🎩 *Snipe Amount:* {setting.amount_per_snipe} {unit}
                ⚡ *Gas Budget:* {setting.max_gas_price} Gwei
                🔮 *Repeat Purchase:* {'✅' if setting.duplicate_buy else '❌'}
                🌊 *Min. Liquidity:* {setting.min_liquidity}
                ⏳ *Wait Blocks:* {setting.blocks_to_wait}
                🌀 *Trade Slippage:* {setting.slippage} %
                🧐 *Scam Spotter:* {'✅' if setting.hp_toggle else '❌'}

                Remember, accuracy leads to profits. Stay sharp! 🎯
                '''
    return message

# @wallet_menu.callback_query(StartAction.filter(F.type=="wallets"), StateFilter("*"))
@user_settings_menu.callback_query(StartAction.filter(F.type=="user_settings"))
async def bot_network_settings(query: types.CallbackQuery, callback_data: dict):
    message = '''

🛠️ *Sniper Configuration Guide*:

🎩 *Snipe Amount:* Determine how much you're willing to invest per trade.
⚡ *Gas Budget:* Define the upper limit for gas fees on your trades.
🔮 *Repeat Purchase:* Decide if you want to buy the same token multiple times.
🌊 *Min. Liquidity:* Set the minimum liquidity threshold for your trades.
⏳ *Wait Blocks:* Designate a delay before executing a trade in terms of blocks.
🌀 *Trade Slippage:* Adjust your tolerance for price slippage during trades.
🧐 *Scam Spotter:* Toggle the detection mechanism for potential scams.


Select a button below to tailor each setting to your trading strategy. Happy Sniping! 🎯
'''


    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    if not setting:
        network = "ethereum"
        if network == "ethereum":
            setting = default_eth_settings
        elif network == "bsc":
            setting = default_bsc_settings
        else:
            setting = default_arb_settings
        setting = await add_user_settings(query.from_user, setting, db )
        
    message = get_settings_message(setting)
    await query.message.edit_text(text=message, reply_markup=user_settings_keyboard(network="ethereum"))



@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="amount_per_snipe"), StateFilter("*"))
async def amount_per_snipe_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please enter the amount of WETH you'd like to allocate for each new listing snipe:"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="0.01"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.sniper_amount)


@user_settings_menu.message(StateFilter(UserSettingsState.sniper_amount))
async def amount_per_snipe(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = float(messag)
        setting = await state.get_data()
        setting = setting['setting']
        setting.amount_per_snipe = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 0.01, 0.1 etc")
        await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_buy"), StateFilter("*"))
async def auto_buy_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    setting.auto_buy = not setting.auto_buy
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    await query.answer(text="Auto Buy Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="honeypot_settings"), StateFilter("*"))
async def hp_toggle_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    setting.hp_toggle = not setting.hp_toggle if setting.hp_toggle is not None else True
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    await query.answer(text="Scam Detection Settings changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell"), StateFilter("*"))
async def auto_sell_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    setting.auto_sell = not setting.auto_sell
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    await query.answer(text="Auto Sell Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="duplicate_buy"), StateFilter("*"))
async def duplicate_buy_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    setting.duplicate_buy = not setting.duplicate_buy
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    await query.answer(text="Repeat Buy Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell_tp"), StateFilter("*"))
async def auto_sell_tp_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please reply with take profit percentage e.g. 100?"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="100"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_tp)



@user_settings_menu.message(StateFilter(UserSettingsState.set_tp))
async def auto_sell_tp(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = float(messag)
        setting = await state.get_data()
        setting = setting['setting']
        setting.auto_sell_tp = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
        await state.clear()






@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell_sl"), StateFilter("*"))
async def set_sl_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please reply with stop loss percentage e.g. 10?"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_sl)



@user_settings_menu.message(StateFilter(UserSettingsState.set_sl))
async def auto_sell_sl(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.auto_sell_sl = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
        await state.clear()








@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="max_gas_price"), StateFilter("*"))
async def max_gas_price_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please provide the gas price delta: how much extra gas (in Gwei) would you like to add to the current fast gas price? Typically, a value between 3-4 Gwei is recommended."
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="3"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_gas_delta)



@user_settings_menu.message(StateFilter(UserSettingsState.set_gas_delta))
async def max_gas_price(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(int(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.max_gas_price = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
        await state.clear()





@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="min_liquidity"), StateFilter("*"))
async def min_liquidity_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please specify the minimum liquidity addition (in WETH) required to initiate a snipe. For example, you might choose a value like 10. "
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_min_liq)



@user_settings_menu.message(StateFilter(UserSettingsState.set_min_liq))
async def min_liquidity(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.min_liquidity = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="set_slippage_settings"), StateFilter("*"))
async def set_slippage_settings_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = f"Please set slippage for ethereum network in percentage. e.g.: 10, 20%"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_slippage)



@user_settings_menu.message(StateFilter(UserSettingsState.set_slippage))
async def set_slippage_settings(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.slippage = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="set_sell_slippage_settings"), StateFilter("*"))
async def set_sell_slippage_settings_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = f"Please set sell slippage for ethereum network in percentage. e.g.: 10, 20%"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_slippage)



@user_settings_menu.message(StateFilter(UserSettingsState.set_slippage))
async def set_sell_slippage_settings(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.sell_slippage = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()






@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="blocks_to_wait"), StateFilter("*"))
async def blocks_to_wait_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, "ethereum", db)
    message = "Please indicate the number of blocks to wait before executing a buy. For instance, you might choose a value like 3 or 4."
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="3"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_blocks_wait)



@user_settings_menu.message(StateFilter(UserSettingsState.set_blocks_wait))
async def blocks_to_wait(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.blocks_to_wait = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network))
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 2, 3 etc")  
    await state.clear()



# for update copy trade percentage 
@user_settings_menu.callback_query(UserSettingsAction.filter(F.column == "updatecopytradepercentage"))
async def updatecopytradepercentage(query:CallbackQuery , state:FSMContext):
    users_IID = query.from_user.id
    await query.message.reply(f"UPDATE THE PERCENTAGE OF ETHERUM YOU WANT TO INVEST ! " , reply_markup=ForceReply(input_field_placeholder="Enter percentage %"))
    await state.set_state('percentage_of_etherum_update')

@user_settings_menu.message(StateFilter("percentage_of_etherum_update"))
async def percentage_of_etherum_update(message:types.Message)->None:
    userId = message.from_user.id
    percentage = message.text
    await updateCopyTradePercentage(userId , percentage )
    backto_settings = backbutton_to_setting()
    await message.answer(f"YOUR INVESTMENT OF ETHERUM IS UPDATED NOW!" , reply_markup=backto_settings.as_markup())


# # for starting copy trading percentage taking 
@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="startcopytradebtn"))
async def startcopytradebtn(query:CallbackQuery , state:FSMContext):
#     # if the percentage is given already do not use that function
    users_IID = query.from_user.id
  
    user_percentage = await get_percentgae_of_copy_trade(users_IID)
    if user_percentage:
        user_id = query.from_user.id
       
        
        total_Adress,len = await get_no_of_addresses(user_id)
        add_address = addaddresskeyboard(len)
        await query.message.delete()
        if len == 0:
            await query.message.answer(f"REGISTERED COPY TRADING ADDRESSES ARE {len} \n YOUR INVESTMENT PERCENTAGE : {user_percentage}" , reply_markup=add_address.as_markup())
        elif len == 1:
            await query.message.answer(f"REGISTERED COPY TRADING ADDRESSES ARE {len} \n YOUR INVESTMENT PERCENTAGE : {user_percentage} \n 1):YOUR EXISTING WALLET ADDRESS IS: ❕❗ {total_Adress[0]}" , reply_markup=add_address.as_markup())
        else:
            await query.message.answer(f"REGISTERED COPY TRADING ADDRESSES LIMIT IS EXCEEDED: \n YOUR INVESTMENT PERCENTAGE : {user_percentage}   \n 1):YOUR EXISTING WALLET ADDRESS IS: ❕❗ {total_Adress[0]} \n 2):YOUR EXISTING SECOND WALLET ADDRESSS: ❕❗ {total_Adress[1]} " , reply_markup=add_address.as_markup())

    else: 
       


        await query.message.reply(f"ENTER THE PERCENTAGE OF ETHERUM YOU WANT TO INVEST! " , reply_markup=ForceReply(input_field_placeholder="Enter percentage %"))
        await state.set_state('percentage_of_etherum')
    

# for starting of copy trading  buttons 
@user_settings_menu.message(StateFilter("percentage_of_etherum"))
async def start_copy_trade_btn(message:types.Message)->None:
    
    userId = message.from_user.id
    percentage = message.text
    

    await updateCopyTradePercentage(userId , percentage )

    total_Adress,len = await get_no_of_addresses(userId)
    
    
    add_address = addaddresskeyboard(len)

    await message.delete()
    
    if len == 0:
        await message.answer(f"REGISTERED COPY TRADING ADDRESSES ARE  {len} \n YOUR INVESTMENT PERCENTAGE : {percentage} " , reply_markup=add_address.as_markup())
    elif len == 1:
        await message.answer(f"REGISTERED COPY TRADING ADDRESSES ARE {len} \n YOUR INVESTMENT PERCENTAGE : {percentage} \n 1):YOUR EXISTING WALLET ADDRESS IS: ❕❗ {total_Adress[0]}" , reply_markup=add_address.as_markup())
    else:
        await message.answer(f"REGISTERED COPY TRADING ADDRESSES LIMIT IS EXCEEDED: \n YOUR INVESTMENT PERCENTAGE : {percentage}   \n 1):YOUR EXISTING WALLET ADDRESS IS: ❕❗ {total_Adress[0]} \n 2):YOUR EXISTING SECOND WALLET ADDRESSS: ❕❗ {total_Adress[1]} " , reply_markup=add_address.as_markup())


# add copy  address 
@user_settings_menu.callback_query(btnfortradecopy.filter(F.strt=="addaddress"))
async def addaddress(query:CallbackQuery , state: FSMContext)->None:
    await query.message.reply(f"you are going to add the address " , reply_markup=ForceReply(input_field_placeholder="0x41qwd...qweq456"))
    await state.set_state('addaddress')




# delete copy address 
@user_settings_menu.callback_query(btnfortradecopy.filter(F.strt=="deleteaddress"))
async def deleteAddress(query:CallbackQuery , state:FSMContext)->None:
    await query.message.reply(f"Enter the address to delete " , reply_markup=ForceReply(input_field_placeholder="0x41qwd...qweq456"))
    await state.set_state('deleteaddress')




@user_settings_menu.message(StateFilter("addaddress"))
async def handle_message_for_addaddress(message: types.Message)->None:
    backing_to_settings = InlineKeyboardBuilder()
    backing_to_settings.button(text="🔙 Back Menu", callback_data=StartAction(type="user_settings").pack())
    backing_to_settings.adjust(1)


    user_text = message.text
    user_id = message.from_user.id

    pattern_address = re.compile(r'^0x[a-fA-F0-9]{40}$')
    is_valid_address = bool(pattern_address.match(user_text))
    if is_valid_address:
        result = await addcopytradingaddress(user_id , user_text)
        if result:
            await message.reply(text="YOUR ADDRESS HAS BEEN ADDED" , reply_markup=backing_to_settings.as_markup())
        else: 
            await message.reply(text="No User Found" , reply_markup=backing_to_settings.as_markup())
    else:
        
        backing_to_settings = InlineKeyboardBuilder()
        backing_to_settings.button(text="🔙 Back Menu", callback_data=StartAction(type="user_settings").pack())
        backing_to_settings.adjust(1)
        await message.answer(f"you have enter the wrong address or wrong address pattern", reply_markup=backing_to_settings.as_markup())




@user_settings_menu.message(StateFilter("deleteaddress"))
async def handle_message_for_deleteaddress(message:types.Message)->None:
    backing_to_settings = InlineKeyboardBuilder()
    backing_to_settings.button(text="🔙 Back Menu", callback_data=StartAction(type="user_settings").pack())
    backing_to_settings.adjust(1)
    user_text = message.text
    user_id = message.from_user.id
    result = await deletecopyaddress(user_id , user_text)
    if result:
        await message.reply(text="YOUR ADDRESS HAS BEEN DELETED" , reply_markup=backing_to_settings.as_markup())
    else:
        
        await message.reply(text="TEH ADDRESS OF USER NOT FOUND |OR| CANNOT BE DELETED " , reply_markup=backing_to_settings.as_markup())