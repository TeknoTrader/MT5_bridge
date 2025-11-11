import streamlit as st
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import time

# Page configuration
st.set_page_config(page_title="MT5 Trading App - Filtered", layout="wide")

# Initialize session state at the beginning
if 'connected' not in st.session_state:
    st.session_state['connected'] = False
if 'account_info' not in st.session_state:
    st.session_state['account_info'] = None
if 'filter_comment' not in st.session_state:
    st.session_state['filter_comment'] = "Streamlit Trade"

st.title("📈 MT5 Trading Application - With Comment Filter")
st.markdown("---")

# Sidebar for account configuration
with st.sidebar:
    st.header("⚙️ MT5 Account Configuration")

    account_number = st.number_input("Account Number", min_value=0, value=0, step=1)
    password = st.text_input("Password", type="password")
    server = st.text_input("Server", value="")

    st.markdown("---")

    if st.button("🔌 Connect to MT5", use_container_width=True):
        if not mt5.initialize():
            st.error(f"❌ MT5 initialization failed: {mt5.last_error()}")
            st.session_state['connected'] = False
        else:
            authorized = mt5.login(account_number, password=password, server=server)
            if authorized:
                st.success("✅ Connection successful!")
                st.session_state['connected'] = True
                account_info = mt5.account_info()
                if account_info:
                    st.session_state['account_info'] = account_info
                    st.info(f"💰 Balance: {account_info.balance} {account_info.currency}")
                    st.info(f"📊 Equity: {account_info.equity} {account_info.currency}")
            else:
                st.error(f"❌ Login failed: {mt5.last_error()}")
                st.session_state['connected'] = False
                st.session_state['account_info'] = None

    if st.button("🔌 Disconnect", use_container_width=True):
        mt5.shutdown()
        st.session_state['connected'] = False
        st.session_state['account_info'] = None
        st.info("Disconnected from MT5")

    # Show connection status
    st.markdown("---")
    if st.session_state['connected']:
        st.success("🟢 Connected")
    else:
        st.warning("🔴 Not connected")

# Main area - Trading interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💹 Trading Panel")

    # Trade parameter inputs
    symbol = st.text_input("Symbol", value="EURUSD", help="Enter the symbol to trade (e.g.: EURUSD, GBPUSD)")

    col_size, col_sl, col_tp = st.columns(3)

    with col_size:
        lot_size = st.number_input("Size (Lots)", min_value=0.01, value=0.1, step=0.01, format="%.2f")

    with col_sl:
        stop_loss = st.number_input("Stop Loss (pips)", min_value=0, value=0, step=1)

    with col_tp:
        take_profit = st.number_input("Take Profit (pips)", min_value=0, value=0, step=1)

    comment = st.text_input("Comment (to identify trades)", value="Streamlit Trade",
                            help="Enter a unique comment to filter only this app's trades")

    # Save comment in session state for filtering
    if comment:
        st.session_state['filter_comment'] = comment

    st.markdown("---")

    # BUY and SELL buttons
    col_buy, col_sell = st.columns(2)

    with col_buy:
        if st.button("🟢 BUY", use_container_width=True, type="primary"):
            if not st.session_state.get('connected', False):
                st.error("❌ You are not connected to MT5! Connect from the sidebar.")
            else:
                with st.spinner("Sending BUY order..."):
                    try:
                        # Prepare trade request
                        symbol_info = mt5.symbol_info(symbol)
                        if symbol_info is None:
                            st.error(f"❌ Symbol {symbol} not found")
                        else:
                            if not symbol_info.visible:
                                if not mt5.symbol_select(symbol, True):
                                    st.error(f"❌ Cannot select symbol {symbol}")
                                    st.stop()

                            point = symbol_info.point
                            price = mt5.symbol_info_tick(symbol).ask

                            # Calculate SL and TP
                            sl = price - stop_loss * point * 10 if stop_loss > 0 else 0
                            tp = price + take_profit * point * 10 if take_profit > 0 else 0

                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": lot_size,
                                "type": mt5.ORDER_TYPE_BUY,
                                "price": price,
                                "sl": sl,
                                "tp": tp,
                                "deviation": 20,
                                "magic": 234000,
                                "comment": comment,
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }

                            # Send order
                            result = mt5.order_send(request)

                            if result is None:
                                st.error(f"❌ BUY order failed: {mt5.last_error()}")
                            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                                st.error(f"❌ BUY order failed: {result.retcode} - {result.comment}")
                            else:
                                st.success(f"✅ BUY order executed successfully!")
                                st.balloons()
                                st.info(f"🎫 Ticket: {result.order}")
                                st.info(f"💰 Volume: {result.volume} lots")
                                st.info(f"💵 Price: {result.price}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    with col_sell:
        if st.button("🔴 SELL", use_container_width=True, type="secondary"):
            if not st.session_state.get('connected', False):
                st.error("❌ You are not connected to MT5! Connect from the sidebar.")
            else:
                with st.spinner("Sending SELL order..."):
                    try:
                        # Prepare trade request
                        symbol_info = mt5.symbol_info(symbol)
                        if symbol_info is None:
                            st.error(f"❌ Symbol {symbol} not found")
                        else:
                            if not symbol_info.visible:
                                if not mt5.symbol_select(symbol, True):
                                    st.error(f"❌ Cannot select symbol {symbol}")
                                    st.stop()

                            point = symbol_info.point
                            price = mt5.symbol_info_tick(symbol).bid

                            # Calculate SL and TP
                            sl = price + stop_loss * point * 10 if stop_loss > 0 else 0
                            tp = price - take_profit * point * 10 if take_profit > 0 else 0

                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": lot_size,
                                "type": mt5.ORDER_TYPE_SELL,
                                "price": price,
                                "sl": sl,
                                "tp": tp,
                                "deviation": 20,
                                "magic": 234000,
                                "comment": comment,
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }

                            # Send order
                            result = mt5.order_send(request)

                            if result is None:
                                st.error(f"❌ SELL order failed: {mt5.last_error()}")
                            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                                st.error(f"❌ SELL order failed: {result.retcode} - {result.comment}")
                            else:
                                st.success(f"✅ SELL order executed successfully!")
                                st.balloons()
                                st.info(f"🎫 Ticket: {result.order}")
                                st.info(f"💰 Volume: {result.volume} lots")
                                st.info(f"💵 Price: {result.price}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

with col2:
    st.header("📊 Open Positions")

    # COMMENT FILTER
    st.markdown("#### 🔍 Display Filter")
    filter_enabled = st.checkbox("Show only positions with specific comment", value=False)

    if filter_enabled:
        filter_comment_input = st.text_input(
            "Comment to filter",
            value=st.session_state.get('filter_comment', 'Streamlit Trade'),
            help="Display only positions with this comment"
        )
        st.info(f"🔎 Active filter: '{filter_comment_input}'")
    else:
        filter_comment_input = None
        st.info("📋 Showing all positions")

    st.markdown("---")

    # AUTO-REFRESH
    col_refresh1, col_refresh2 = st.columns([1, 1])

    with col_refresh1:
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=False)

    with col_refresh2:
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Interval (seconds)",
                options=[1, 2, 3, 5, 10, 30],
                index=2,  # default 3 seconds
                key="refresh_interval"
            )
        else:
            refresh_interval = 5

    if auto_refresh:
        st.info(f"⏱️ Refreshing every {refresh_interval} seconds")
        import time

        time.sleep(refresh_interval)
        st.rerun()

    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()

    if st.session_state.get('connected', False):
        try:
            # Retrieve all positions
            all_positions = mt5.positions_get()

            if all_positions is None or len(all_positions) == 0:
                st.info("No open positions")
            else:
                # Filter positions if filter is active
                if filter_enabled and filter_comment_input:
                    filtered_positions = [pos for pos in all_positions if pos.comment == filter_comment_input]
                else:
                    filtered_positions = list(all_positions)

                # Show statistics
                total_positions = len(all_positions)
                filtered_count = len(filtered_positions)

                if filter_enabled and filter_comment_input:
                    st.caption(f"Filtered positions: {filtered_count} / {total_positions} total")
                else:
                    st.caption(f"Total positions: {total_positions}")

                if len(filtered_positions) == 0:
                    if filter_enabled:
                        st.warning(f"⚠️ No positions found with comment '{filter_comment_input}'")
                    else:
                        st.info("No open positions")
                else:
                    # Calculate total profit of filtered positions
                    total_profit = sum([pos.profit for pos in filtered_positions])
                    profit_color = "🟢" if total_profit >= 0 else "🔴"
                    st.metric("Total Profit (filtered)", f"{profit_color} {total_profit:.2f}")

                    # Button to close ALL filtered positions
                    if len(filtered_positions) > 1:
                        st.markdown("---")
                        if st.button(f"⚠️ CLOSE ALL {len(filtered_positions)} POSITIONS",
                                     type="primary",
                                     use_container_width=True,
                                     key="close_all"):
                            with st.spinner(f"Closing {len(filtered_positions)} positions..."):
                                closed_count = 0
                                failed_count = 0

                                for pos in filtered_positions:
                                    try:
                                        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                                        tick = mt5.symbol_info_tick(pos.symbol)

                                        if tick is None:
                                            failed_count += 1
                                            continue

                                        close_price = tick.bid if pos.type == 0 else tick.ask

                                        close_request = {
                                            "action": mt5.TRADE_ACTION_DEAL,
                                            "symbol": pos.symbol,
                                            "volume": pos.volume,
                                            "type": close_type,
                                            "position": pos.ticket,
                                            "price": close_price,
                                            "deviation": 20,
                                            "magic": 234000,
                                            "comment": f"Close All {pos.ticket}",
                                            "type_time": mt5.ORDER_TIME_GTC,
                                            "type_filling": mt5.ORDER_FILLING_IOC,
                                        }

                                        result = mt5.order_send(close_request)

                                        if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
                                            closed_count += 1
                                        else:
                                            failed_count += 1

                                    except Exception:
                                        failed_count += 1

                                if closed_count > 0:
                                    st.success(f"✅ {closed_count} positions closed successfully!")
                                if failed_count > 0:
                                    st.warning(f"⚠️ {failed_count} positions not closed")

                                st.balloons()
                                time.sleep(1)
                                st.rerun()

                    st.markdown("---")

                    # Display filtered positions
                    for pos in filtered_positions:
                        with st.expander(f"#{pos.ticket} - {pos.symbol} {'🟢' if pos.profit >= 0 else '🔴'}"):
                            col_info1, col_info2 = st.columns(2)

                            with col_info1:
                                st.write(f"**Type:** {'BUY' if pos.type == 0 else 'SELL'}")
                                st.write(f"**Volume:** {pos.volume} lots")
                                st.write(f"**Open price:** {pos.price_open}")
                                st.write(f"**Current price:** {pos.price_current}")

                            with col_info2:
                                profit_color = "🟢" if pos.profit >= 0 else "🔴"
                                st.write(f"**Profit:** {profit_color} {pos.profit:.2f}")
                                st.write(f"**SL:** {pos.sl if pos.sl > 0 else 'N/A'}")
                                st.write(f"**TP:** {pos.tp if pos.tp > 0 else 'N/A'}")
                                st.write(f"**Comment:** {pos.comment}")

                            st.markdown("---")

                            # Button to close position
                            if st.button(f"❌ Close Position #{pos.ticket}", key=f"close_{pos.ticket}",
                                         type="secondary", use_container_width=True):
                                with st.spinner(f"Closing position #{pos.ticket}..."):
                                    try:
                                        # Determine closure type (opposite to opening type)
                                        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY

                                        # Get current price
                                        tick = mt5.symbol_info_tick(pos.symbol)
                                        if tick is None:
                                            st.error(f"❌ Cannot get price for {pos.symbol}")
                                        else:
                                            close_price = tick.bid if pos.type == 0 else tick.ask

                                            # Create closure request
                                            close_request = {
                                                "action": mt5.TRADE_ACTION_DEAL,
                                                "symbol": pos.symbol,
                                                "volume": pos.volume,
                                                "type": close_type,
                                                "position": pos.ticket,
                                                "price": close_price,
                                                "deviation": 20,
                                                "magic": 234000,
                                                "comment": f"Close {pos.ticket}",
                                                "type_time": mt5.ORDER_TIME_GTC,
                                                "type_filling": mt5.ORDER_FILLING_IOC,
                                            }

                                            # Send closure request
                                            result = mt5.order_send(close_request)

                                            if result is None:
                                                st.error(f"❌ Closure failed: {mt5.last_error()}")
                                            elif result.retcode != mt5.TRADE_RETCODE_DONE:
                                                st.error(f"❌ Closure failed: {result.retcode} - {result.comment}")
                                            else:
                                                st.success(f"✅ Position #{pos.ticket} closed successfully!")
                                                st.info(f"💰 Final profit: {pos.profit:.2f}")
                                                st.balloons()
                                                time.sleep(1)
                                                st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Closure error: {str(e)}")

        except Exception as e:
            st.error(f"Error retrieving positions: {str(e)}")
    else:
        st.warning("⚠️ Connect to MT5 to view positions")

# Footer
st.markdown("---")
st.caption("⚠️ WARNING: This is a real trading application. Use with caution!")
st.caption("💡 TIP: Use unique comments to identify trades from this application and filter them easily!")
