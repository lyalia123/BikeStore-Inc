# add_coordinates.py
import psycopg2
import requests
import time
from geopy.geocoders import Nominatim

def add_coordinates_to_stores():
    """Добавляет координаты к магазинам на основе адресов"""
    
    # Подключение к БД
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="bikestore",
        user="postgres",
        password="Alpieva2006"
    )
    cur = conn.cursor()
    
    # Добавляем колонки если их нет
    print("Добавляем колонки координат...")
    cur.execute("""
        ALTER TABLE stores 
        ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 6),
        ADD COLUMN IF NOT EXISTS longitude DECIMAL(10, 6);
    """)
    
    # Получаем магазины без координат
    cur.execute("""
        SELECT store_id, store_name, street, city, state, zip_code 
        FROM stores 
        WHERE latitude IS NULL OR longitude IS NULL;
    """)
    
    stores = cur.fetchall()
    print(f"Найдено {len(stores)} магазинов для обновления координат")
    
    # Инициализируем геокодер
    geolocator = Nominatim(user_agent="bikestore_analytics")
    
    for store in stores:
        store_id, store_name, street, city, state, zip_code = store
        
        # Формируем адрес
        address = f"{street}, {city}, {state}, {zip_code}"
        print(f"Обрабатываем: {address}")
        
        try:
            # Геокодируем адрес
            location = geolocator.geocode(address)
            
            if location:
                # Обновляем координаты в БД
                cur.execute("""
                    UPDATE stores 
                    SET latitude = %s, longitude = %s 
                    WHERE store_id = %s
                """, (location.latitude, location.longitude, store_id))
                
                print(f"✅ {store_name}: {location.latitude}, {location.longitude}")
            else:
                # Если не нашли координаты, используем координаты по умолчанию для города
                default_coords = get_default_coordinates(city, state)
                cur.execute("""
                    UPDATE stores 
                    SET latitude = %s, longitude = %s 
                    WHERE store_id = %s
                """, (default_coords['lat'], default_coords['lng'], store_id))
                
                print(f"⚠️  {store_name}: использованы координаты по умолчанию")
            
            # Пауза чтобы не превысить лимиты API
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Ошибка для {store_name}: {e}")
            # Используем координаты по умолчанию в случае ошибки
            default_coords = get_default_coordinates(city, state)
            cur.execute("""
                UPDATE stores 
                SET latitude = %s, longitude = %s 
                WHERE store_id = %s
            """, (default_coords['lat'], default_coords['lng'], store_id))
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Координаты добавлены для всех магазинов!")

def get_default_coordinates(city, state):
    """Возвращает координаты по умолчанию для известных городов"""
    default_coords = {
        'New York': {'lat': 40.7128, 'lng': -74.0060},
        'Los Angeles': {'lat': 34.0522, 'lng': -118.2437},
        'Chicago': {'lat': 41.8781, 'lng': -87.6298},
        'Houston': {'lat': 29.7604, 'lng': -95.3698},
        'Phoenix': {'lat': 33.4484, 'lng': -112.0740},
        'Philadelphia': {'lat': 39.9526, 'lng': -75.1652},
        'San Antonio': {'lat': 29.4241, 'lng': -98.4936},
        'San Diego': {'lat': 32.7157, 'lng': -117.1611},
        'Dallas': {'lat': 32.7767, 'lng': -96.7970},
        'San Jose': {'lat': 37.3382, 'lng': -121.8863}
    }
    
    # Пробуем найти по городу, потом по штату
    if city in default_coords:
        return default_coords[city]
    elif state in ['NY', 'New York']:
        return {'lat': 40.7128, 'lng': -74.0060}
    elif state in ['CA', 'California']:
        return {'lat': 36.7783, 'lng': -119.4179}
    elif state in ['IL', 'Illinois']:
        return {'lat': 41.8781, 'lng': -87.6298}
    elif state in ['TX', 'Texas']:
        return {'lat': 31.9686, 'lng': -99.9018}
    else:
        # Координаты по умолчанию (центр США)
        return {'lat': 39.8283, 'lng': -98.5795}

if __name__ == "__main__":
    add_coordinates_to_stores()