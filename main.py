import websocket
import json
import time
from datetime import datetime, timedelta

def on_message(ws, message):
    print(f"받은 메시지: {message}")
    try:
        data = json.loads(message)
        if 'errors' in data:
            print(f"서버 오류: {data['errors']}")
        elif 'type' in data and data['type'] == 'trade':
            analyze_trade(data)
        else:
            print("알 수 없는 메시지 형식")
    except json.JSONDecodeError:
        print("JSON 디코딩 오류. 받은 메시지가 JSON 형식이 아닙니다.")

def on_error(ws, error):
    print(f"에러 발생: {error}")

def on_close(ws):
    print("웹소켓 연결 종료")

def on_open(ws):
    print("웹소켓 연결 성공")
    # API 문서를 참조하여 올바른 구독 메시지 형식을 사용하세요
    subscribe_message = json.dumps({"type": "subscribe", "channel": "trades"})
    ws.send(subscribe_message)

def analyze_trade(trade_data):
    # API 문서를 참조하여 올바른 키 이름을 사용하세요
    wallet_address = trade_data.get('address') or trade_data.get('wallet')
    profit = trade_data.get('profit') or trade_data.get('amount')
    
    if not wallet_address or profit is None:
        print("필요한 데이터가 없습니다.")
        return

    if wallet_address not in wallet_stats:
        wallet_stats[wallet_address] = {'trades': [], 'wins': 0, 'total_profit': 0}
    
    current_time = datetime.now()
    wallet_stats[wallet_address]['trades'].append({'timestamp': current_time, 'profit': profit})
    if profit > 0:
        wallet_stats[wallet_address]['wins'] += 1
    wallet_stats[wallet_address]['total_profit'] += profit

    # 30일 이상 된 데이터 제거
    wallet_stats[wallet_address]['trades'] = [t for t in wallet_stats[wallet_address]['trades'] if current_time - t['timestamp'] <= timedelta(days=30)]

    # 스마트 월렛 조건 확인
    if is_smart_wallet(wallet_address):
        print(f"스마트 월렛 발견: {wallet_address}")

def is_smart_wallet(wallet_address):
    stats = wallet_stats[wallet_address]
    if stats['trades'] < 10:  # 최소 거래 횟수 설정(minimum trading number) 
        return False
    
    win_rate = stats['wins'] / stats['trades']
    avg_profit = stats['total_profit'] / stats['trades']
    
    return win_rate >= 0.9 and avg_profit > 0.5  # 승률 90% 이상, 평균 수익률 50% 이상

wallet_stats = {}

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://pumpportal.fun/api/data",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)

    ws.run_forever()
