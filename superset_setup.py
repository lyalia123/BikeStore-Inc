# superset_setup_fixed.py
import requests
import json
import time

class SupersetSetup:
    def __init__(self):
        self.base_url = "http://localhost:8088"
        self.login_url = f"{self.base_url}/api/v1/security/login"
        self.database_url = f"{self.base_url}/api/v1/database/"
        
        self.session = requests.Session()
        self.access_token = None
        
    def login(self):
        """Аутентификация в Superset"""
        login_payload = {
            "username": "admin",
            "password": "admin",
            "provider": "db",
            "refresh": True
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = self.session.post(self.login_url, json=login_payload, headers=headers)
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                print("✅ Успешная аутентификация в Superset")
                return True
            else:
                print(f"❌ Ошибка аутентификации: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к Superset: {e}")
            return False
    
    def add_database(self):
        """Добавляем подключение к базе данных BikeStore"""
        database_config = {
            "database_name": "BikeStore Database",
            "sqlalchemy_uri": "postgresql://postgres:Alpieva2006@host.docker.internal:5433/bikestore",
            "cache_timeout": 0,
            "expose_in_sqllab": True,
            "allow_run_async": False,
            "allow_ctas": True,
            "allow_cvas": True,
            "allow_dml": False,
            "allow_file_upload": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            print("🔄 Добавляем подключение к базе данных...")
            response = self.session.post(self.database_url, json=database_config, headers=headers)
            if response.status_code in [200, 201]:
                print("✅ База данных успешно добавлена в Superset")
                return True
            else:
                print(f"❌ Ошибка добавления БД: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка при добавлении БД: {e}")
            return False
    
    def setup_complete(self):
        """Полная настройка Superset"""
        print("🔄 Начинаем настройку подключения к БД...")
        if self.login():
            time.sleep(2)
            if self.add_database():
                print("✅ Настройка Superset завершена!")
                print("🌐 Доступ: http://localhost:8088")
                print("🔑 Логин: admin / Пароль: admin")
            else:
                print("❌ Не удалось добавить базу данных")
        else:
            print("❌ Не удалось авторизоваться в Superset")

if __name__ == "__main__":
    print("⏳ Ожидание запуска Superset...")

    # Проверяем, доступен ли Superset каждые 10 секунд
    setup = SupersetSetup()
    for i in range(12):  # максимум 12 попыток = 2 минуты
        try:
            r = requests.get("http://localhost:8088/health")
            if r.status_code == 200:
                print("✅ Superset готов к подключению!")
                break
        except Exception:
            print(f"⏳ Superset еще не запущен... попытка {i + 1}/12")
        time.sleep(10)
    else:
        print("❌ Superset не запустился за 2 минуты. Проверь контейнер.")
        exit(1)

    setup.setup_complete()
