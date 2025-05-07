import requests # 用於發送API請求
import json     # 用於處理JSON數據
import google.generativeai as genai # Google Gemini AI API

# --- 設定您的 Google Gemini API 資訊 ---
# 警告：請勿將您的真實 API 金鑰直接寫在程式碼中並上傳到公開倉庫。
# 建議使用環境變數或安全的組態管理方式。
GEMINI_API_KEY = "AIzaSyDvn69EHMpKvcNC-g2UBdarYGWo1XiIApk"

# 配置Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# 創建Gemini模型
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# 預設參數 (如果API調用失敗或未提供某些值，則使用這些預設值)
DEFAULT_WALKING_SPEED_MPS = 1.4
DEFAULT_SECONDS_PER_PERSON = 0.5
MIN_GREEN_LIGHT_SECONDS = 5.0
MAX_GREEN_LIGHT_SECONDS = 60.0

def get_dynamic_parameters_from_ai(road_width_meters: float, num_people: int, current_time: str = None, weather: str = None) -> dict:
    """
    調用 Google Gemini API 以獲取動態調整的計算參數。

    參數:
    road_width_meters (float): 道路寬度（公尺）。
    num_people (int):          偵測到的行人數。
    current_time (str, optional): 當前時間 (例如 "17:30")。
    weather (str, optional):      當前天氣 (例如 "rainy")。

    返回:
    dict: 包含 'walking_speed_mps' 和 'seconds_per_person' 的字典。
          如果API調用失敗，則返回預設參數。
    """
    # 構建提示訊息，描述情境並請求參數
    time_context = f"時間是 {current_time}" if current_time else "未提供時間信息"
    weather_context = f"天氣是 {weather}" if weather else "未提供天氣信息"
    
    prompt = f"""
作為一個交通管理AI專家，我需要你分析以下行人穿越道路的情況，並提供適合的參數：

- 道路寬度：{road_width_meters} 公尺
- 等待穿越的行人數：{num_people} 人
- {time_context}
- {weather_context}

請為這種情況提供以下兩個參數：
1. 估計的行人行走速度（公尺/秒）- 考慮道路狀況、人流密度、時間及天氣因素
2. 每位行人應增加的綠燈秒數

請只回覆JSON格式的數據，格式如下：
{{
  "suggested_walking_speed_mps": 數值,
  "suggested_seconds_per_person": 數值
}}

普通成人在理想情況下的平均行走速度約為1.4公尺/秒，每增加一位行人大約需要增加0.5秒的綠燈時間。
請根據情境適當調整這些值。例如，如果是雨天或行人較多，行走速度可能降低；如果是學校區域，可能需要更長的每人秒數。
"""

    print(f"發送請求: 道路寬度 {road_width_meters}m, {num_people}人")

    try:
        # 調用Gemini API
        response = gemini_model.generate_content(prompt)
        
        # 提取回應文本
        response_text = response.text.strip()
        
        try:
            # 嘗試解析JSON回應
            # 由於Gemini有時會在JSON前後添加額外文本，我們需要提取JSON部分
            # 尋找JSON開始和結束的大括號
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                api_data = json.loads(json_str)
                
                # 提取建議的參數值
                walking_speed = api_data.get("suggested_walking_speed_mps", DEFAULT_WALKING_SPEED_MPS)
                seconds_per_person = api_data.get("suggested_seconds_per_person", DEFAULT_SECONDS_PER_PERSON)
                
                return {
                    "walking_speed_mps": float(walking_speed),
                    "seconds_per_person": float(seconds_per_person),
                }
            else:
                raise ValueError("無法解析JSON")
        
        except:
            return {
                "walking_speed_mps": DEFAULT_WALKING_SPEED_MPS,
                "seconds_per_person": DEFAULT_SECONDS_PER_PERSON,
            }

    except:
        return {
            "walking_speed_mps": DEFAULT_WALKING_SPEED_MPS,
            "seconds_per_person": DEFAULT_SECONDS_PER_PERSON,
        }


def calculate_green_light_seconds_with_ai(
    road_width_meters: float,
    num_people: int,
    walking_speed_mps: float, # 由 Gemini API 或預設值提供
    seconds_per_person: float # 由 Gemini API 或預設值提供
) -> float:
    """
    根據 (可能由AI調整過的) 參數計算建議的綠燈秒數。

    參數:
    road_width_meters (float): 道路寬度（公尺）。
    num_people (int):          行人數量。
    walking_speed_mps (float): AI建議或預設的行人步行速度（公尺/秒）。
    seconds_per_person (float): AI建議或預設的每位行人增加秒數。

    返回:
    float: 計算出的綠燈秒數，限制在 MIN_GREEN_LIGHT_SECONDS 和 MAX_GREEN_LIGHT_SECONDS 之間。
    """
    calculated_seconds = (road_width_meters / walking_speed_mps) + (num_people * seconds_per_person)
    final_green_light_seconds = max(MIN_GREEN_LIGHT_SECONDS, min(calculated_seconds, MAX_GREEN_LIGHT_SECONDS))
    return final_green_light_seconds

# --- 測試範例 ---
if __name__ == "__main__":
    # 模擬從攝影機或其他感測器獲取的數據
    current_road_width = 15.0  # 公尺
    detected_pedestrians = 30  # 人

    # 1. 從 Gemini API 獲取動態參數
    # 您可以傳遞更多上下文資訊給 Gemini API，例如時間和天氣
    print("\n--- 高人流情境 ---")
    dynamic_params = get_dynamic_parameters_from_ai(
        current_road_width, 
        detected_pedestrians, 
        current_time="08:30", 
        weather="clear"
    )

    ai_walking_speed = dynamic_params["walking_speed_mps"]
    ai_seconds_per_person = dynamic_params["seconds_per_person"]

    print(f"參數: 步行速度 = {ai_walking_speed:.2f} m/s, 每人秒數 = {ai_seconds_per_person:.2f} s")

    # 2. 使用從 Gemini API 獲取 (或預設) 的參數來計算綠燈秒數
    green_time = calculate_green_light_seconds_with_ai(
        current_road_width,
        detected_pedestrians,
        ai_walking_speed,
        ai_seconds_per_person
    )
    print(f"建議綠燈秒數: {green_time:.2f} 秒")

    # 另一個測試案例：低人流
    print("\n--- 低人流情境 ---")
    current_road_width_low = 8.0
    detected_pedestrians_low = 5
    dynamic_params_low = get_dynamic_parameters_from_ai(
        current_road_width_low, 
        detected_pedestrians_low,
        current_time="10:30",
        weather="rainy"
    )
    green_time_low = calculate_green_light_seconds_with_ai(
        current_road_width_low,
        detected_pedestrians_low,
        dynamic_params_low["walking_speed_mps"],
        dynamic_params_low["seconds_per_person"]
    )
    print(f"建議綠燈秒數: {green_time_low:.2f} 秒")

    # 提醒：如果您的 Google Gemini API 端點或金鑰無效，程式將使用預設參數。
    # 請確保替換 GEMINI_API_KEY。
    if GEMINI_API_KEY == "在此填入您的Google Gemini API金鑰":
        print("\n*** 警告: 您尚未使用真實的 Google Gemini API 金鑰。目前使用的是預設參數或模擬的API調用。 ***")
        print("*** 請修改程式碼中的 GEMINI_API_KEY。 ***")

