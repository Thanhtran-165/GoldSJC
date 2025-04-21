import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import sqlite3
from vnstock.explorer.misc import sjc_gold_price, vcb_exchange_rate
from tabulate import tabulate
from colorama import init, Fore, Style

# Khởi tạo colorama để hỗ trợ màu sắc trên Windows
init(autoreset=True)

def check_internet_connection():
    """Kiểm tra kết nối internet."""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        print(f"{Fore.RED}Lỗi: Không có kết nối internet.{Style.RESET_ALL}")
        return False

def fetch_web_data():
    """Tải nội dung HTML từ trang web Trading Economics."""
    url = "https://tradingeconomics.com/commodities"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    return response.content if response.status_code == 200 else None

def clean_major_name(major):
    """Làm sạch tên hàng hóa để so sánh chính xác."""
    return major.split("\n\n")[0].strip() if "\n\n" in major else major.strip()

def format_value(value):
    """Định dạng giá trị để luôn có 2 chữ số sau dấu thập phân."""
    if "." in value:
        integer_part, decimal_part = value.split(".", 1)
        return f"{integer_part}.{decimal_part.zfill(2)}"
    return f"{value}.00"

def get_world_gold_price():
    """Trích xuất giá vàng thế giới từ Trading Economics (USD/ounce)."""
    html_content = fetch_web_data()
    if not html_content:
        print(f"{Fore.RED}Lỗi: Không thể tải dữ liệu từ Trading Economics.{Style.RESET_ALL}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) < 2:
        print(f"{Fore.RED}Lỗi: Không tìm thấy bảng dữ liệu trên Trading Economics.{Style.RESET_ALL}")
        return None

    table = tables[1]  # Bảng thứ hai chứa thông tin giá vàng
    rows = table.find_all('tr')[1:]  # Bỏ qua hàng tiêu đề

    for row in rows:
        cols = [col.text.strip() for col in row.find_all(['td', 'th'])]
        if cols and clean_major_name(cols[0]) == "Gold":
            price = cols[1]  # Giá nằm ở cột thứ hai
            formatted_price = format_value(price)
            try:
                return float(formatted_price)
            except ValueError:
                print(f"{Fore.RED}Lỗi: Không thể chuyển đổi giá vàng '{formatted_price}' sang số.{Style.RESET_ALL}")
                return None

    print(f"{Fore.RED}Lỗi: Không tìm thấy giá vàng trên Trading Economics.{Style.RESET_ALL}")
    return None

def get_vnd_exchange_rate():
    """Lấy tỷ giá USD/VND từ Vietcombank."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        exchange_rate = vcb_exchange_rate(date=today)
        if not exchange_rate.empty:
            usd_row = exchange_rate[exchange_rate['currency_code'] == 'USD']
            if not usd_row.empty:
                value = str(usd_row['sell'].values[0]).replace(',', '')
                return float(value)
            else:
                print(f"{Fore.RED}Lỗi: Không có dữ liệu tỷ giá USD.{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Lỗi: Dữ liệu tỷ giá rỗng.{Style.RESET_ALL}")
            return None
    except Exception as e:
        print(f"{Fore.RED}Lỗi khi lấy tỷ giá USD/VND: {e}{Style.RESET_ALL}")
        return None

def get_sjc_gold_price():
    """Lấy giá vàng SJC."""
    try:
        sjc_price = sjc_gold_price()
        if not sjc_price.empty:
            value = str(sjc_price['sell_price'].iloc[0]).replace(',', '')
            return float(value)
        else:
            print(f"{Fore.RED}Lỗi: Dữ liệu giá vàng SJC rỗng.{Style.RESET_ALL}")
            return None
    except Exception as e:
        print(f"{Fore.RED}Lỗi khi lấy giá vàng SJC: {e}{Style.RESET_ALL}")
        return None

def convert_ounce_to_cay(price_per_ounce, exchange_rate):
    """Chuyển đổi giá vàng từ ounce sang cây (1 ounce = 1.20565303 cây)."""
    try:
        if price_per_ounce is None or exchange_rate is None:
            print(f"{Fore.RED}Lỗi: Giá vàng hoặc tỷ giá là None.{Style.RESET_ALL}")
            return None
        price_per_cay = price_per_ounce * exchange_rate * 1.20565303
        return price_per_cay
    except Exception as e:
        print(f"{Fore.RED}Lỗi chuyển đổi ounce sang cây: {e}{Style.RESET_ALL}")
        return None

def init_database():
    """Khởi tạo database và bảng nếu chưa tồn tại."""
    conn = sqlite3.connect('gold_prices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gold_prices
                 (timestamp TEXT, world_gold_price REAL, vnd_exchange_rate REAL, sjc_gold_price REAL, basic_percentage REAL)''')
    conn.commit()
    conn.close()

def save_to_database(timestamp, world_gold_price, vnd_exchange_rate, sjc_gold_price, basic_percentage):
    """Lưu dữ liệu vào database."""
    conn = sqlite3.connect('gold_prices.db')
    c = conn.cursor()
    c.execute("INSERT INTO gold_prices VALUES (?, ?, ?, ?, ?)", 
              (timestamp, world_gold_price, vnd_exchange_rate, sjc_gold_price, basic_percentage))
    conn.commit()
    conn.close()

def get_previous_data(current_timestamp):
    """Lấy dữ liệu của lần cập nhật trước đó."""
    conn = sqlite3.connect('gold_prices.db')
    c = conn.cursor()
    c.execute("SELECT * FROM gold_prices WHERE timestamp < ? ORDER BY timestamp DESC LIMIT 1", (current_timestamp,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'timestamp': row[0],
            'world_gold_price': row[1],
            'vnd_exchange_rate': row[2],
            'sjc_gold_price': row[3],
            'basic_percentage': row[4]
        }
    return None

def get_update_interval():
    """Hiển thị menu để người dùng chọn thời gian cập nhật."""
    print(f"{Fore.CYAN}Chọn thời gian cập nhật:{Style.RESET_ALL}")
    print("1. 1 phút\n2. 5 phút\n3. 10 phút")
    choice = input("Nhập lựa chọn (1-3): ")
    intervals = {'1': 60, '2': 300, '3': 600}
    return intervals.get(choice, 60)  # Mặc định 1 phút nếu nhập sai

def main():
    """Chương trình chính."""
    print(f"{Fore.CYAN}=== Ứng dụng theo dõi giá vàng ==={Style.RESET_ALL}")
    print("Hiển thị giá vàng thế giới, giá SJC và chênh lệch theo thời gian thực.")
    print(f"{Fore.YELLOW}Nhấn Ctrl+C để thoát bất cứ lúc nào.{Style.RESET_ALL}")
    
    if not check_internet_connection():
        print(f"{Fore.RED}Không thể tiếp tục do không có kết nối internet.{Style.RESET_ALL}")
        return

    update_interval = get_update_interval()
    print(f"{Fore.CYAN}Chương trình sẽ tự động cập nhật sau mỗi {update_interval} giây.{Style.RESET_ALL}")

    # Khởi tạo database
    init_database()

    while True:
        try:
            # Lấy timestamp hiện tại
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Lấy dữ liệu từ các nguồn
            world_gold_price = get_world_gold_price()
            vnd_exchange_rate = get_vnd_exchange_rate()
            sjc_gold_price_value = get_sjc_gold_price()

            # Kiểm tra dữ liệu hợp lệ
            if all(v is not None for v in [world_gold_price, vnd_exchange_rate, sjc_gold_price_value]):
                # Chuyển đổi giá vàng thế giới sang VND/cây
                world_gold_price_vnd = convert_ounce_to_cay(world_gold_price, vnd_exchange_rate)
                
                if world_gold_price_vnd is not None:
                    # Tính toán chênh lệch
                    basic_percentage = ((sjc_gold_price_value - world_gold_price_vnd) / world_gold_price_vnd) * 100
                    
                    # Lưu dữ liệu vào database
                    save_to_database(current_timestamp, world_gold_price_vnd, vnd_exchange_rate, sjc_gold_price_value, basic_percentage)
                    
                    # Lấy dữ liệu trước đó
                    previous_data = get_previous_data(current_timestamp)
                    
                    # Khởi tạo các chuỗi thay đổi và màu sắc
                    if previous_data:
                        world_gold_change = world_gold_price_vnd - previous_data['world_gold_price']
                        sjc_change = sjc_gold_price_value - previous_data['sjc_gold_price']
                        basic_change = basic_percentage - previous_data['basic_percentage']
                        
                        world_gold_change_str = f" ({'↑' if world_gold_change >= 0 else '↓'} {abs(world_gold_change):.2f} VND/cây)"
                        sjc_change_str = f" ({'↑' if sjc_change >= 0 else '↓'} {abs(sjc_change):.2f} VND)"
                        basic_change_str = f" ({'↑' if basic_change >= 0 else '↓'} {abs(basic_change):.2f}%)"
                        
                        world_gold_color = Fore.GREEN if world_gold_change >= 0 else Fore.RED
                        sjc_color = Fore.GREEN if sjc_change >= 0 else Fore.RED
                        basic_color = Fore.GREEN if basic_change >= 0 else Fore.RED
                    else:
                        world_gold_change_str = ""
                        sjc_change_str = ""
                        basic_change_str = ""
                        
                        world_gold_color = Fore.YELLOW
                        sjc_color = Fore.YELLOW
                        basic_color = Fore.YELLOW
                    
                    # Hiển thị kết quả với bảng và màu sắc
                    data = [
                        [Fore.YELLOW + "Giá vàng thế giới theo VND" + Style.RESET_ALL, 
                         world_gold_color + f"{world_gold_price_vnd:.2f} VND/cây" + Style.RESET_ALL + world_gold_change_str],
                        [Fore.YELLOW + "Giá vàng SJC" + Style.RESET_ALL, 
                         sjc_color + f"{sjc_gold_price_value:.2f} VND" + Style.RESET_ALL + sjc_change_str],
                        [Fore.YELLOW + "Chênh lệch (Basic)" + Style.RESET_ALL, 
                         basic_color + f"{basic_percentage:.2f}%" + Style.RESET_ALL + basic_change_str]
                    ]
                    print(f"\n{Fore.CYAN}Cập nhật giá vàng lúc {current_timestamp}:{Style.RESET_ALL}")
                    print(tabulate(data, headers=[Fore.CYAN + 'Thông tin' + Style.RESET_ALL, Fore.CYAN + 'Giá trị' + Style.RESET_ALL], tablefmt="fancy_grid"))
                    
                    # Hiển thị thông tin bổ sung
                    print(f"{Fore.MAGENTA}Thông tin bổ sung:{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Giá vàng thế giới (XAU): {world_gold_price:.2f} USD/ounce{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Tỷ giá USD/VND: {vnd_exchange_rate:.2f} VND/USD{Style.RESET_ALL}")
                    print(f"{Fore.MAGENTA}Giá chưa bao gồm các loại phí và thuế.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Lỗi chuyển đổi giá vàng.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Thiếu dữ liệu từ một hoặc nhiều nguồn.{Style.RESET_ALL}")

            # Tự động cập nhật sau khoảng thời gian đã chọn
            time.sleep(update_interval)

        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}Đã thoát chương trình.{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Lỗi không xác định: {e}{Style.RESET_ALL}")
            time.sleep(update_interval)

if __name__ == "__main__":
    main()