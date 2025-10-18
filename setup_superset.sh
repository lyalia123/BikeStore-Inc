# setup_superset.sh
#!/bin/bash

# Создаем docker-compose файл
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  superset:
    image: apache/superset:latest
    container_name: superset
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=bikestore-superset-secret-key-2024
    volumes:
      - superset_data:/app/superset_home
    depends_on:
      - postgres

  postgres:
    image: postgres:13
    container_name: superset_postgres
    environment:
      - POSTGRES_DB=superset
      - POSTGRES_USER=superset
      - POSTGRES_PASSWORD=superset
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  superset_data:
  postgres_data:
EOF

# Запускаем контейнеры
docker-compose up -d

# Ждем запуска
sleep 30

# Инициализируем Superset
docker exec -it superset superset db upgrade
docker exec -it superset superset init

# Создаем администратора
docker exec -it superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@bikestore.com \
  --password admin

echo "Superset запущен на http://localhost:8088"
echo "Логин: admin"
echo "Пароль: admin"