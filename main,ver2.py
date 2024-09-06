import websocket
import json
import time
from datetime import datetime, timedelta

# 로그 파일에 기록하는 함수 (utf-8 인코딩 사용)
def log_message(message):
    with open("log.txt", "a", encoding='utf-8') as log_file:
        log_file.write(f"{datetime.now()}: {message}\n")

def on_message(ws, message):
    print(f"받은 메시지: {message}")
    log_message(f"Received message: {message}")
    
    try:
        data = json.loads(message)
        # 메시지의 구조에 따른 처리
        if 'errors' in data:
            error_message = f"서버 오류: {data['errors']}"
            print(error_message)
            log_message(error_message)
        elif 'txType' in data and data['txType'] == 'create':
            analyze_trade(data)  # 새로운 거래 분석 함수 호출
        elif 'message' in data:
            # 구독 성공 메시지 처리
            log_message(f"Subscription message: {data['message']}")
        else:
            print("알 수 없는 메시지 형식")
            log_message("Unknown message format received")
    except json.JSONDecodeError:
        error_message = "JSON 디코딩 오류. 받은 메시지가 JSON 형식이 아닙니다."
        print(error_message)
        log_message(error_message)

def on_error(ws, error):
    print(f"에러 발생: {error}")
    log_message(f"Error occurred: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"웹소켓 연결 종료. 상태 코드: {close_status_code}, 메시지: {close_msg}")
    log_message(f"Websocket connection closed. Status Code: {close_status_code}, Message: {close_msg}")

def on_open(ws):
    print("웹소켓 연결 성공")
    log_message("Websocket connection opened")
    
    # 토큰 생성 이벤트 구독
    subscribe_message = json.dumps({
        "method": "subscribeNewToken",
    })
    ws.send(subscribe_message)
    log_message(f"Sent subscription message: {subscribe_message}")
    
    # 특정 계정의 거래 구독
    subscribe_account_message = json.dumps({
        "method": "subscribeAccountTrade",
        "keys": ["AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV"]
    })
    ws.send(subscribe_account_message)
    log_message(f"Sent subscription message for account trade: {subscribe_account_message}")
    
    # 특정 토큰의 거래 구독
    subscribe_token_message = json.dumps({
        "method": "subscribeTokenTrade",
        "keys": ["91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p"]
    })
    ws.send(subscribe_token_message)
    log_message(f"Sent subscription message for token trade: {subscribe_token_message}")

def analyze_trade(trade_data):
    # 거래 데이터 분석 처리 (기존 로직)
    wallet_address = trade_data.get('traderPublicKey') or trade_data.get('wallet')
    profit = trade_data.get('initialBuy') or trade_data.get('amount')
    
    if not wallet_address or profit is None:
        print("필요한 데이터가 없습니다.")
        log_message("Missing required data in trade")
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
        smart_wallet_message = f"스마트 월렛 발견: {wallet_address}"
        print(smart_wallet_message)
        log_message(smart_wallet_message)
        send_alert(smart_wallet_message)

def is_smart_wallet(wallet_address):
    stats = wallet_stats[wallet_address]
    if len(stats['trades']) < 10:  # 최소 거래 횟수 설정
        return False
    
    win_rate = stats['wins'] / len(stats['trades'])
    avg_profit = stats['total_profit'] / len(stats['trades'])
    
    return win_rate >= 0.9 and avg_profit > 0.5  # 승률 90% 이상, 평균 수익률 50% 이상

# 알림을 기록하는 함수 (utf-8 인코딩 사용)
def send_alert(message):
    alert_message = f"ALERT: {message}"
    print(alert_message)
    with open("alert.txt", "a", encoding='utf-8') as alert_file:
        alert_file.write(f"{datetime.now()}: {alert_message}\n")

wallet_stats = {}

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://pumpportal.fun/api/data",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)

    ws.run_forever()
